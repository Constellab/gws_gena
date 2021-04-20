# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math

from gws.logger import Error
from gws.model import Process
from gena.network import Network, Compound, Reaction, ReactionDuplicate
from gena.data import ECData, BiomassData

class DraftRecon(Process):
    input_specs = { 'ec_data': (ECData,), 'biomass_data': (BiomassData, None) }
    output_specs = { 'network': (Network,) }
    config_specs = {
        'tax_id': {"type": 'str', "default": '', "description": "The taxonomy id"},
        'tax_search_method': {"type": 'str', "default": 'bottom_up', "description": "If 'bottom_up', the algorithm will to traverse the taxonomy tree to search in the higher taxonomy levels until a reaction is found. If 'none', the algorithm will only search at the given taxonomy level given by `tax_id`"}
    }
    
    async def task(self):
        net = self._create_network()
        rxns = self._create_biomass_equation(net)
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
                net.data["errors"].append({
                    "ec_number": ec,
                    "reason": "partial_ec_number"
                })
            else:
                try:
                    Reaction.from_biota(ec_number=ec, network=net, tax_id=tax_id)
                except Exception as err:
                    net.data["errors"].append({
                        "ec_number": ec,
                        "reason": str(err)
                    })
        return net
    
    def _create_biomass_equation(self, net):
        rxns = []
        biomass_comps = self._create_biomass_compounds(net)
        self._create_biomass_rxns(net, biomass_comps)
        
    def _create_biomass_rxns(self, net, biomass_comps):
        biomass_data = self.input['biomass_data']
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
                net.data["errors"].append({
                    "ec_number": col_name,
                    "reason": error_message
                })
                
    def _create_biomass_compounds(self, net):
        biomass_data = self.input['biomass_data']
        row_names = biomass_data.row_names
        chebi_ids = biomass_data.get_chebi_ids()
        biomass_col_name = biomass_data.biomass_column_name
        
        _comps = []
        i = 0
        for c_id in chebi_ids:
            row_name = row_names[i]
            if row_name == biomass_col_name:
                comp = Compound(name=row_name, compartment="b")
                net.add_compound(comp)
                _comps.append(comp)
            else:
                if not isinstance(c_id, str):
                    c_id = str(c_id)
                    
                if "CHEBI" not in c_id:
                    comp = Compound(name=row_name, compartment="c")
                    net.add_compound(comp)
                    _comps.append(comp)
                else:
                    comp = net.get_compound_by_chebi_id(c_id)
                    if not comp:
                        try:
                            comp = Compound.from_biota(chebi_id = c_id)
                            net.add_compound(comp)
                            _comps.append(comp)
                        except:
                            comp = Compound(name=row_name, chebi_id=c_id, compartment="c")
                            net.add_compound(comp)
                            _comps.append(comp)
                            #raise Error("DraftRecon", "_create_biomass_compounds", f"No compound found for CheBI ID {c_id}")
                    else:
                         _comps.append(comp)
 
            i += 1
   
        return _comps
            
class GapFiller(Process):
    pass