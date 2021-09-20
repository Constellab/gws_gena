# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import Task, task_decorator
from gws_core import Logger
from gws_core import BadRequestException, StrParam, BoolParam, ConfigParams, TaskInputs, TaskOutputs

from gws_biota import Compound as BiotaCompound
from gws_biota import Reaction as BiotaReaction
from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import Taxonomy as BiotaTaxo

from ..network.network import Network
from ..network.compound import Compound
from ..network.reaction import Reaction
from ..twin.twin import Twin
from ..helper.sink_helper import SinkHelper

@task_decorator("GapFiller")
class GapFiller(Task):
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
        'tax_id': StrParam(default_value='', description="The taxonomy id used to fill gaps"),
        'biomass_and_medium_gaps_only': BoolParam(default_value=False, description="True to only fill gaps related to compounds comming from the biomass equation or the medium composition; False otherwise."),
        'add_sink_reactions': BoolParam(default_value=False, description="True to add sink reactions to unresolved dead-end compounds. False otherwise"),
        'skip_cofactors': BoolParam(default_value=True, description="True to skip gaps related to dead-end cofactors. False otherwise"),
        'fill_each_gap_once': BoolParam(default_value=False, description="True to fill each gap with only one putative reaction. False otherwise"),
    }
        
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        output_net = inputs["network"].copy()
        _nb_filled = True
        i = 0
        while True:
            i += 1
            Logger.progress(f"Doing pass {i} ...")
            _nb_filled = self.__fill_gaps_with_tax(output_net, params)
            if _nb_filled <= 1:
                message = f"Pass {i} done: {_nb_filled} gap filled."
            else:
                message = f"Pass {i} done: {_nb_filled} gaps filled."
            if i < 100:
                self.update_progress_value(i+1, message=message)
            Logger.progress(message)
            if not _nb_filled:
                break    
        add_sink_reactions = params["add_sink_reactions"]
        if add_sink_reactions:
            Logger.progress(f"Adding sink reactions ...")
            tf = params["biomass_and_medium_gaps_only"]
            _nb_filled = SinkHelper.fill_gaps_with_sinks(output_net, biomass_and_medium_gaps_only=tf)
            Logger.progress(f"Done: {_nb_filled} gaps filled with sink reactions.")
        return {"network": output_net}

    def __fill_gaps_with_tax(self, net, params):
        _nb_filled = 0
        _gap_info = net._get_gap_info()
        tax_id = params["tax_id"]
        biomass_and_medium_gaps_only = params["biomass_and_medium_gaps_only"]
        skip_cofactors = params["skip_cofactors"]
        fill_each_gap_once = params["fill_each_gap_once"]

        if tax_id:
            try:
                tax = BiotaTaxo.get(BiotaTaxo.tax_id == tax_id)
            except:
                raise BadRequestException(f"No taxonomy found with taxonomy id {tax_id}")
        else:
            tax = None
        for k in _gap_info["compounds"]:
            is_gap = _gap_info["compounds"][k]["is_gap"]
            is_orphan = _gap_info["compounds"][k]["is_orphan"]
            if is_gap and not is_orphan:   # do not deal with orphans
                comp: Compound = net._compounds[k]
                if comp.is_sink:
                    raise BadRequestException("Coherence check. A sink reaction compound should not be a gap compound.")

                if biomass_and_medium_gaps_only:
                    is_in_biomass_or_medium = net.get_compound_tag(comp.id, "is_in_biomass_or_medium")
                    if not is_in_biomass_or_medium:
                        # skip this compound
                        continue

                if not skip_cofactors or not comp.is_cofactor:
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
                            is_rxn_OK = False
                            enzymes = biota_rxn.enzymes
                            for e in enzymes:
                                enzyme_tax_id = getattr(e, "tax_"+tax.rank)
                                if enzyme_tax_id == tax.tax_id:
                                    # an enzyme exists in the taxonomy level
                                    is_rxn_OK = True
                                    break
                        else:
                            is_rxn_OK = True
                        
                        _is_filled_once = False
                        if is_rxn_OK:
                            rxns = Reaction.from_biota(biota_reaction=biota_rxn)
                            
                            # ...
                            # ... @ToDo : check compound id
                            # ...

                            for rxn in rxns:
                                if not net.exists(rxn): # an existing reaction may be given by biota
                                    net.add_reaction(rxn)
                                    net.set_reaction_tag(rxn.id, {
                                        "id": rxn.id,
                                        "is_from_gap_fillering": True
                                    })
                                    _nb_filled += 1
                                    _is_filled_once = True
                                    break #> select only one reaction
                        
                        if fill_each_gap_once and _is_filled_once:
                            break
        return _nb_filled 

    # def __fill_gaps_with_sinks(self, net, params):
    #     _gap_info = net._get_gap_info()
    #     _nb_filled = 0
    #     biomass_and_medium_gaps_only = params["biomass_and_medium_gaps_only"]
    #     for k in _gap_info["compounds"]:
    #         is_gap = _gap_info["compounds"][k]["is_gap"]
    #         is_orphan = _gap_info["compounds"][k]["is_orphan"]
    #         if is_gap and not is_orphan:   # do not deal with orphans
    #             comp: Compound = net._compounds[k]
    #             if comp.is_sink:
    #                 raise BadRequestException("Coherence check. A sink reaction compound should not be a gap compound.")
    #             if biomass_and_medium_gaps_only:
    #                 is_in_biomass_or_medium = net.get_compound_tag(comp.id, "is_in_biomass_or_medium")
    #                 if not is_in_biomass_or_medium:
    #                     # skip this compound
    #                     continue
    #             rxn = Reaction.create_sink_reaction(related_compound=comp)
    #             net.set_reaction_tag(rxn.id, {
    #                 "id": rxn.id,
    #                 "is_from_gap_fillering": True
    #             })
    #             _nb_filled += 1
    #     return _nb_filled