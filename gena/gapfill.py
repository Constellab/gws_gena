# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import copy

from gws.model import Process
from gws.settings import Settings
from gws.logger import Error, Info

from gena.network import Network, Compound, Reaction
from gena.biomodel import Biomodel

from biota.compound import Compound as BiotaCompound
from biota.reaction import Reaction as BiotaReaction
from biota.enzyme import Enzyme as BiotaEnzyme
from biota.taxonomy import Taxonomy as BiotaTaxo

class GapFiller(Process):
    """
    GapFiller class.
    
    This process iteratively fills gap the metabolic networks using the biota DB.
    A gap is detected when an intracellular compound is not a substrate nor a product. 
    The gap filling process consists in the follwing algorithm:
    
    * set `N` = the network
    * for each iteration `i = 0` to `nb_iterations`
      * find all the gap compounds in the network `N`
      * set `nb_gaps` = the number of gaps in `N`
      * if `nb_gaps == 0`, we exit iteration loop
      * for each gap compound, we search for the putative biota reactions in which it is involved
        * for earch reaction, we loop on all the enzymes realated to the reaction
          * if `tax_id` parameter is given, we fill the gap with the corresponding reaction only if the enzyme exists at this taxonomy level (i.e. the reaction is added to `N`). The reaction is not added otherwise.
          * if `tax_id` is not given, we do not check the taxonomy tree, we fill the gap with this reaction and the reaction is added to `N`.
        * continue
      * continue
      
    At the end of the process all the reactions existing in the biota DB able to fill the gaps will the add the the network.
    """
    
    input_specs = { 'network': (Network,) }
    output_specs = { 'network': (Network,) }
    config_specs = {
        'tax_id': {"type": 'str', "default": '', "description": "The taxonomy id"},
        'nb_iterations': {"type": 'int', "default": 3, "description": "Number of gap filling iterations"},
    }
    
    async def task(self):
        input_net = self.input["network"]
        output_net = Network.from_json(input_net.dumps())
        nb_iter = self.get_param("nb_iterations")
        self.progress_bar.set_max_value(nb_iter)
        
        _nb_filled = True
        for i in range(0,nb_iter):
            _nb_filled = self.__fill_gaps(output_net)
            
            if _nb_filled <= 1:
                message = f"Iteration {i+1}: {_nb_filled} gap filled"
            else:
                message = f"Iteration {i+1}: {_nb_filled} gaps filled"
                
            self.progress_bar.set_value(i+1, message=message)
            Info(message)
            
            if not _nb_filled:
                break
            
        self.output["network"] = output_net
        
    
    def __comp_info(self, net):
        _comps = {}
        for k in net._compounds:
            _comps[k] = {
                "is_substrate": False,
                "is_product": False
            }
            
        for k in net._reactions:
            rxn = net._reactions[k]
            for c_id in rxn._substrates:
                comp = rxn._substrates[c_id]["compound"]
                _comps[comp.id]["is_substrate"] = True
                
            for c_id in rxn._products:
                comp = rxn._products[c_id]["compound"]
                _comps[comp.id]["is_product"] = True
        
        return _comps
    
    def __fill_gaps(self, net):
        _nb_filled = 0
        _comps = self.__comp_info(net)
        tax_id = self.get_param("tax_id")
        
        if tax_id:
            try:
                tax = BiotaTaxo.get(BiotaTaxo.tax_id == tax_id)
            except:
                raise Error("GapFiller", "__fill_gaps", f"No taxonomy found with taxonomy id {tax_id}")
        else:
            tax = None
            
        for k in _comps:
            if not _comps[k]["is_product"] or not _comps[k]["is_substrate"]:
                comp = net._compounds[k]
                
                if comp.is_intracellular:
                    if not comp.chebi_id in Compound.COFACTORS:
                        try:
                            biota_c = BiotaCompound.get(BiotaCompound.chebi_id == comp.chebi_id)
                        except Exception as err:
                            net.set_compound_tag(comp.id, {
                                "id": comp.id,
                                "is_chebi_not_found": True,
                                "error": "Chebi id not found"
                            })
    
                        for biota_r in biota_c.reactions:
                            if tax:
                                OK = False
                                enzymes = biota_r.enzymes
                                for e in enzymes:
                                    enzyme_tax_id = getattr(e, "tax_"+tax.rank)
                                    if enzyme_tax_id == tax.tax_id:
                                        # an enzyme exists in the taxonomy level
                                        OK = True
                                        break
                                
                                if not OK:
                                    #> search in ancestors
                                    pass
                            else:
                                OK = True
                            
                            if OK:
                                rxns = Reaction.from_biota(biota_reaction=biota_r)
                                for rxn in rxns:
                                    if not net.exists(rxn):
                                        _nb_filled += 1
                                        net.add_reaction(rxn)

                                        net.set_reaction_tag(rxn.id, {
                                            "id": rxn.id,
                                            "is_gap_filled": True
                                        })
     
        return _nb_filled 