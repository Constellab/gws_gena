# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math
from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs, OptionalIn, StrParam
from gws_core import BadRequestException
from gws_biota import (Enzyme as BiotaEnzyme, 
                        Reaction as BiotaReaction,
                        Taxonomy as BiotaTaxo)
from ..network.network import Network, ReactionDuplicate, CompoundDuplicate
from ..network.compound import Compound
from ..network.reaction import Reaction
from ..data.biomass_table import BiomassTable
from ..data.medium_table import MediumTable
from ..data.ec_number_table import ECNumberTable

@task_decorator("DraftRecon")
class DraftRecon(Task):
    """
    DraftRecon class.
    
    This process performs a draft reconstruction of the metabolic network using a list of ec numbers.
    
    * for each `ec_number`, we find all the corresponding enzymes from the biota DB. If the `tax_id` is also given, we only retrieve enzyme that match the `ec_number` and the taxonomy.
      * if enzymes found
        * for each enzyme
          * we add the corresponding reaction to the network
          * continue
      * if no enzyme found
        * if `tax_id` is given and `tax_search_method == bottom_up`, we traverse the taxonomy tree above the `tax_id` of retrieve all the enzymes matching against the `ec_number`.
        * for each enzyme
          * we add the reaction corresponding the lowest taxonomy lever (i.e. closest to `tax_id`)
          * break the current loop
      * continue
      
    At the end of the process all the possible reactions existing in the biota DB will be added to the draft network.
    """
    
    input_specs = { 
        'ec_number_table': OptionalIn(ECNumberTable,), 
        'biomass_table': OptionalIn(BiomassTable), 
        'medium_table': OptionalIn(MediumTable) 
    }
    output_specs = { 'network': (Network,) }
    config_specs = {
        'tax_id': StrParam(default_value='', human_name="Taxonomy ID", short_description="The NCBI taxonomy id"),
        'tax_search_method': StrParam(default_value='bottom_up', human_name="Taxonomy search method", short_description="If 'bottom_up', the algorithm will to traverse the taxonomy tree to search in the higher taxonomy levels until a reaction is found. If 'none', the algorithm will only search at the given taxonomy level given by `tax_id`")
    }
    
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        self._params = params
        self._inputs = inputs
        net = self._create_network()
        self._create_biomass_equation(net)
        self._create_culture_medium(net)
        return {"network" : net}

    def _create_network(self):
        tax_id = self._params['tax_id']
        if 'ec_number_table' in self._inputs:
            return self._create_network_with_ec_list()
        elif tax_id:
            return self._create_network_without_ec_list()
        else:
            raise BadRequestException("A list of EC numbers or a taxonomy ID is required")

    def _create_network_without_ec_list(self):
        tax_id = self._params['tax_id']
        tax_search_method = self._params['tax_search_method']
        try:
            tax = BiotaTaxo.get(BiotaTaxo.tax_id == tax_id)
        except:
            raise BadRequestException(f"No taxonomy found with tax_id {tax_id}")
        
        enzymes = BiotaEnzyme.select(BiotaEnzyme.ec_number.distinct()).where( 
            getattr(BiotaEnzyme, "tax_"+tax.rank) == tax.tax_id,  
        )

        total_enzymes = len(enzymes)
        self.log_info_message(f"{total_enzymes} enzymes found")
        net = Network()
        counter = 1
        nb_interval = int(total_enzymes/10)
        perc = 0
        self.update_progress_value(perc, message=f"enzyme {counter} ...")
        for enzyme in enzymes:
            if (counter % nb_interval) == 0:
                perc = 100*(counter/total_enzymes)
                self.update_progress_value(perc, message=f"enzyme {counter} ...")
            try:
                Reaction.from_biota(ec_number=enzyme.ec_number, network=net, tax_id=tax_id, tax_search_method=tax_search_method)
            except Exception as err:
                pass
                # net.set_reaction_tag(enzyme.ec_number, {
                #     "ec_number": enzyme.ec_number,
                #     "error": str(err)
                # })
            counter+=1
        return net

    def _create_network_with_ec_list(self):
        ec_number_table = self._inputs['ec_number_table']
        tax_id = self._params['tax_id']
        ec_list = ec_number_table.get_ec_numbers(rtype="list")
        tax_search_method = self._params['tax_search_method']
        net = Network()
        
        total_enzymes = len(ec_list)
        self.log_info_message(f"{total_enzymes} enzymes to process")
        counter = 1
        nb_interval = int(total_enzymes/10)
        perc = 0
        self.update_progress_value(perc, message=f"enzyme {counter} ...")
        for ec in ec_list:
            if (counter % nb_interval) == 0:
                perc = 100*(counter/total_enzymes)
                self.update_progress_value(perc, message=f"enzyme {counter} ...")

            ec = str(ec).strip()
            is_incomplete_ec = ("-" in ec)
            if is_incomplete_ec:
                net.set_reaction_tag(ec, {
                    "ec_number": ec,
                    "is_partial_ec_number": True,
                    "error": "Partial ec number"
                })
            else:
                try:
                    Reaction.from_biota(ec_number=ec, network=net, tax_id=tax_id, tax_search_method=tax_search_method)
                except Exception as err:
                    net.set_reaction_tag(ec, {
                        "ec_number": ec,
                        "error": str(err)
                    })
            counter+=1
        return net
    
    def _create_biomass_equation(self, net):
        biomass_comps = self._create_biomass_compounds(net)
        self._create_biomass_rxns(net, biomass_comps)
    
    def _create_culture_medium(self, net):
        if 'medium_table' not in self._inputs:
            return

        medium_table = self._inputs['medium_table']
        row_names = medium_table.row_names
        #col_names = medium_table.column_names
        chebi_ids = medium_table.get_chebi_ids()
        i = 0
        for chebi_id in chebi_ids:    
            name = row_names[i]
            subs = self._retrieve_or_create_comp(net, chebi_id, name, compartment=Compound.COMPARTMENT_EXTRACELL)
            prod = self._retrieve_or_create_comp(net, chebi_id, name, compartment=Compound.COMPARTMENT_CYTOSOL)
            try:
                rxn = Reaction(
                    id=prod.name+"_ex", 
                    network=net
                )
                rxn.add_product(prod, 1)
                rxn.add_substrate(subs, 1)
            except ReactionDuplicate:
                # ... the reactoin alread exits => OK!
                pass
            except Exception as err:
                raise BadRequestException(f"Cannot create culture medium reactions. Exception: {err}")
                
            i += 1
            
    def _create_biomass_rxns(self, net, biomass_comps):
        if 'biomass_table' not in self._inputs:
            return

        biomass_table = self._inputs['biomass_table']
        col_names = biomass_table.column_names
        chebi_col_name = biomass_table.chebi_column_name        
        for col_name in col_names:
            if col_name == chebi_col_name:
                continue  
            rxn = Reaction(id=col_name, direction="R", lower_bound = 0.0)
            coefs = biomass_table.get_column(col_name)
            error_message = "The reaction is empty"
            for i in range(0,len(coefs)):
                if isinstance(coefs[i], str):
                    coefs[i] = coefs[i].strip()
                    if not coefs[i]:
                        continue
                    try:
                        stoich = float(coefs[i])
                    except:
                        error_message = f"Coefficient '{coefs[i]}' is not a valid float"
                        break
                else:
                    if math.isnan(coefs[i]):
                        continue 
                    stoich = coefs[i]
                comp = biomass_comps[i]
                if stoich > 0:
                    rxn.add_product(comp, stoich)
                else:
                    rxn.add_substrate(comp, stoich)
            if not rxn.is_empty:
                net.add_reaction(rxn)
            else:
                ec = col_name
                net.set_reaction_tag(ec, {
                    "ec_number": ec,
                    "error": error_message
                })
                
    def _create_biomass_compounds(self, net):
        if 'biomass_table' not in self._inputs:
            return

        biomass_table = self._inputs['biomass_table']
        row_names = biomass_table.row_names
        chebi_ids = biomass_table.get_chebi_ids()
        biomass_col_name = biomass_table.biomass_column_name
        _comps = []
        i = 0
        for chebi_id in chebi_ids:
            name = row_names[i]
            if name == biomass_col_name:
                comp = Compound(name=name, compartment=Compound.COMPARTMENT_BIOMASS)
                _comps.append(comp)
            else:
                comp = self._retrieve_or_create_comp(net, chebi_id, name, compartment=Compound.COMPARTMENT_CYTOSOL)
                _comps.append(comp)  
            i += 1
        if not net.exists(comp):
            net.add_compound(comp)
        return _comps
    
    @staticmethod
    def _retrieve_or_create_comp(net, chebi_id, name, compartment):
        if not isinstance(chebi_id, str):
            chebi_id = str(chebi_id)    
        chebi_id = chebi_id.upper()
        if "CHEBI" not in chebi_id:
            comp = Compound(name=name, compartment=compartment)
        else:   
            comp = net.get_compound_by_chebi_id(chebi_id, compartment=compartment)  
            if not comp:
                try:
                    comp = Compound.from_biota(chebi_id = chebi_id, compartment=compartment) 
                except:
                    #invalid chebi_id
                    comp = Compound(name=name, compartment=compartment) 
        
        if not net.exists(comp):
            net.add_compound(comp)
        net.set_compound_tag(comp.id, {
            "id": comp.id,
            "is_in_biomass_or_medium": True
        })
        return comp