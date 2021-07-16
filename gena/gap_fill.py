# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import copy

from gws.process import Process
from gws.settings import Settings
from gws.logger import Error, Info

from biota.compound import Compound as BiotaCompound
from biota.reaction import Reaction as BiotaReaction
from biota.enzyme import Enzyme as BiotaEnzyme
from biota.taxonomy import Taxonomy as BiotaTaxo

from .compound import Compound
from .reaction import Reaction
from .network import Network
from .biomodel import BioModel

class GapFiller(Process):
    """
    GapFiller class.
    
    This process iteratively fills gaps realted to dead-end compound using the biota DB.
    A gap is detected when an steady compound is a dead-end compound. 
    The gap filling process consists in the follwing algorithm:
    
    * set `N` = the network
    * Loop
      * find all the gap compounds in the network `N`
      * set `nb_gaps` = the number of gaps in `N`
      * if `nb_gaps == 0`, we exit the Loop
      * set `nb_filled = 0`
      * for each gap compound, we search for the putative biota reactions in which it is involved
        * for earch reaction, we loop on all the enzymes related to the reaction
          * if `tax_id` parameter is given, we fill the gap with the corresponding reaction only if the enzyme exists at this taxonomy level (i.e. the reaction is added to `N`). The reaction is not added otherwise. Set `nb_filled = nb_filled+1`.
          * if `tax_id` is not given, we do not check the taxonomy tree, we fill the gap with this reaction and the reaction is added to `N`. Set `nb_filled = nb_filled+1`.
      * if `nb_filled == 0`, we exit the Loop
    * 
    At the end of the process all the reactions existing in the biota DB able to fill the gaps will the add the the network.
    """
    
    input_specs = { 'network': (Network,) }
    output_specs = { 'network': (Network,) }
    config_specs = {
        'tax_id': {"type": 'str', "default": '', "description": "The taxonomy id"},
        'biomass_and_medium_gaps_only': {"type": 'bool', "default": False, "description": "True to only fill gaps related to compounds comming from the biomass equation or the medium composition; False otherwise."},
        'add_sink_reactions': {"type": 'bool', "default": False, "description": "True add sink reactions to unresolved dead-end compounds. False otherwise"},
    }
        
    async def task(self):        
        input_net = self.input["network"]
        output_net = Network.from_json(input_net.dumps())
        _nb_filled = True
        i = 0
        while True:
            i += 1
            Info(f"Doing pass {i} ...")
            _nb_filled = self.__fill_gaps(output_net)
            if _nb_filled <= 1:
                message = f"Pass {i} done: {_nb_filled} gap filled."
            else:
                message = f"Pass {i} done: {_nb_filled} gaps filled."
            if i < self.progress_bar.get_max_value():
                self.progress_bar.set_value(i+1, message=message)
            Info(message)
            if not _nb_filled:
                break    
        add_sink_reactions = self.get_param("add_sink_reactions")
        if add_sink_reactions:
            Info(f"Adding sink reactions ...")
            _nb_filled = self.__fill_gaps_with_sinks(output_net)
            Info(f"Done: {_nb_filled} gaps filled with sink reactions.")
        self.output["network"] = output_net

    def __fill_gaps(self, net):
        _nb_filled = 0
        _gap_info = net._get_gap_info()
        tax_id = self.get_param("tax_id")
        biomass_and_medium_gaps_only = self.get_param("biomass_and_medium_gaps_only")
        if tax_id:
            try:
                tax = BiotaTaxo.get(BiotaTaxo.tax_id == tax_id)
            except:
                raise Error("GapFiller", "__fill_gaps", f"No taxonomy found with taxonomy id {tax_id}")
        else:
            tax = None
        for k in _gap_info["compounds"]:
            if _gap_info["compounds"][k]["is_gap"]:
                comp: Compound = net._compounds[k]
                if comp.is_sink:
                    raise Error("GapFiller", "__fill_gaps", "Coherence check. A sink reaction compound should not be a gap compound.")

                if biomass_and_medium_gaps_only:
                    is_in_biomass_or_medium = net.get_compound_tag(comp.id, "is_in_biomass_or_medium")
                    if not is_in_biomass_or_medium:
                        # skip this compound
                        continue
                if not comp.is_cofactor:
                    try:
                        biota_c = BiotaCompound.get(BiotaCompound.chebi_id == comp.chebi_id)
                    except Exception as _:
                        net.set_compound_tag(comp.id, {
                            "id": comp.id,
                            "is_chebi_not_found": True,
                            "error": "Chebi id not found"
                        })
                        continue
                    for biota_rxn in biota_c.reactions:
                        if tax:
                            is_rxn_found_in_biota = False
                            enzymes = biota_rxn.enzymes
                            for e in enzymes:
                                enzyme_tax_id = getattr(e, "tax_"+tax.rank)
                                if enzyme_tax_id == tax.tax_id:
                                    # an enzyme exists in the taxonomy level
                                    is_rxn_found_in_biota = True
                                    break
                        else:
                            is_rxn_found_in_biota = True
                        if is_rxn_found_in_biota:
                            rxns = Reaction.from_biota(biota_reaction=biota_rxn)
                            for rxn in rxns:
                                if not net.exists(rxn): # an existing reaction may be given by biota
                                    net.add_reaction(rxn)
                                    net.set_reaction_tag(rxn.id, {
                                        "id": rxn.id,
                                        "is_from_gap_filling": True
                                    })
                                    _nb_filled += 1
        return _nb_filled 

    def __fill_gaps_with_sinks(self, net):
        _gap_info = net._get_gap_info()
        _nb_filled = 0
        biomass_and_medium_gaps_only = self.get_param("biomass_and_medium_gaps_only")
        for k in _gap_info["compounds"]:
            if _gap_info["compounds"][k]["is_gap"]:
                comp: Compound = net._compounds[k]
                if comp.is_sink:
                    raise Error("GapFiller", "__fill_gaps", "Coherence check. A sink reaction compound should not be a gap compound.")
                if biomass_and_medium_gaps_only:
                    is_in_biomass_or_medium = net.get_compound_tag(comp.id, "is_in_biomass_or_medium")
                    if not is_in_biomass_or_medium:
                        # skip this compound
                        continue
                rxn = Reaction.create_sink_reaction(related_compound=comp)
                net.set_reaction_tag(rxn.id, {
                    "id": rxn.id,
                    "is_from_gap_filling": True
                })
                _nb_filled += 1
        return _nb_filled