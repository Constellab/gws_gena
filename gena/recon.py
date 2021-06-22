# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math
from gws.logger import Error, Info
from gws.model import Process
from gena.network import Network, Compound, Reaction, ReactionDuplicate, CompoundDuplicate
from gena.data import ECData, BiomassData, MediumData

class DraftRecon(Process):
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
    
    input_specs = { 'ec_data': (ECData,), 'biomass_data': (BiomassData, None), 'medium_data': (MediumData, None) }
    output_specs = { 'network': (Network,) }
    config_specs = {
        'tax_id': {"type": 'str', "default": '', "description": "The taxonomy id"},
        'tax_search_method': {"type": 'str', "default": 'bottom_up', "description": "If 'bottom_up', the algorithm will to traverse the taxonomy tree to search in the higher taxonomy levels until a reaction is found. If 'none', the algorithm will only search at the given taxonomy level given by `tax_id`"}
    }
    
    async def task(self):
        net = self._create_network()
        self._create_biomass_equation(net)
        self._create_culture_medium(net)
        self.output["network"] = net
     
    def _create_network(self):
        ec_data = self.input['ec_data']
        ec_list = ec_data.get_ec_numbers(rtype="list")
        
        net = Network()
        tax_id = self.get_param('tax_id')
        
        for ec in ec_list:
            ec = str(ec).strip()
            is_incomplete_ec = ("-" in ec)
            
            if is_incomplete_ec:
                net.set_reaction_tag(ec, {
                    "ec_number": ec,
                    "is_partial_ec_number": True,
                    "error": "Partial ec number"
                })
                #net.data["logs"]["reactions"].append({
                #    "ec_number": ec,
                #    "reason": "partial_ec_number"
                #})
            else:
                try:
                    Reaction.from_biota(ec_number=ec, network=net, tax_id=tax_id)
                except Exception as err:
                    net.set_reaction_tag(ec, {
                        "ec_number": ec,
                        "error": str(err)
                    })
                    #net.data["logs"]["reactions"].append({
                    #    "ec_number": ec,
                    #    "reason": str(err)
                    #})
        return net
    
    def _create_biomass_equation(self, net):
        rxns = []
        biomass_comps = self._create_biomass_compounds(net)
        self._create_biomass_rxns(net, biomass_comps)
    
    def _create_culture_medium(self, net):
        medium_data = self.input['medium_data']
        if not medium_data:
            return
        
        row_names = medium_data.row_names
        col_names = medium_data.column_names
        chebi_ids = medium_data.get_chebi_ids()

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
                raise Error("DraftRecon", "_create_culture_medium", f"Unexpected error. Exception: {err}")
                
            i += 1
            
    def _create_biomass_rxns(self, net, biomass_comps):
        biomass_data = self.input['biomass_data']
        if not biomass_data:
            return
        
        col_names = biomass_data.column_names
        chebi_ids = biomass_data.get_chebi_ids()
        
        chebi_col_name = biomass_data.chebi_column_name
        biomass_col_name = biomass_data.biomass_column_name
        
        for col_name in col_names:
            if col_name == chebi_col_name:
                continue
                
            rxn = Reaction(id=col_name, direction="R", lower_bound = 0.0)
            coefs = biomass_data.get_column(col_name)
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
                #net.data["logs"]["reactions"].append({
                #    "ec_number": col_name,
                #    "reason": error_message
                #})
                
    def _create_biomass_compounds(self, net):
        biomass_data = self.input['biomass_data']
        row_names = biomass_data.row_names
        chebi_ids = biomass_data.get_chebi_ids()
        biomass_col_name = biomass_data.biomass_column_name
        
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
            comps = net.get_compounds_by_chebi_id(chebi_id, compartment=compartment)  
            if not comps:
                try:
                    comp = Compound.from_biota(chebi_id = chebi_id, compartment=compartment)
                    
                except:
                    #invalid chebi_id
                    comp = Compound(name=name, compartment=compartment) 
            else:
                comp = comps[0]
        
        if not net.exists(comp):
            net.add_compound(comp)
            
        net.set_compound_tag(comp.id, {
            "id": comp.id,
            "is_in_biomass_or_medium": True
        })
            
        return comp