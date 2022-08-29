# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_biota import Compound as BiotaCompound
from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import Reaction as BiotaReaction
from gws_biota import Taxonomy as BiotaTaxo
from gws_core import (BadRequestException, BoolParam, ConfigParams, InputSpec,
                      Logger, OutputSpec, StrParam, Task, TaskInputs,
                      TaskOutputs, task_decorator)

from ..network.compound.compound import Compound
from ..network.network import Network
from ..network.reaction.reaction import Reaction
from .helper.gap_finder_helper import GapFinderHelper


@task_decorator("GapFiller_001", human_name="Gap filler", short_description="Fills gaps in a networks")
class GapFiller(Task):
    """
    GapFiller class.

    This process iteratively fills gaps related to dead-end compounds using the biota DB.
    A gap is detected if a steady compound is a dead-end compound.
    The gap filling algorithm consists in the following steps:

    * set `N` = the network
    * Loop
      * find all the gap compounds in the network `N`
      * set `nb_gaps` = the number of gaps in `N`
      * if `nb_gaps == 0`, we exit the Loop
      * set `nb_filled = 0`
      * for each gap compound, we search for the putative biota reactions in which it is involved
        * for each reaction, we loop on all the enzymes related to the reaction
          * if `tax_id` parameter is given, we fill the gaps with the reactions if the reaction is found at this taxonomy. Set `nb_filled = nb_filled+1`.
          * if `tax_id` is not given, we do not check the taxonomy tree, we fill the gap with this reaction and the reaction is added to `N`. Set `nb_filled = nb_filled+1`.
      * if `nb_filled == 0`, we exit the Loop
    *
    At the end of the process all the reactions existing in the biota DB able to fill the gaps will the add the the network.
    """

    input_specs = {
        'network': InputSpec(Network, human_name="Network", short_description="The network to gap-fill")
    }

    output_specs = {
        'network': OutputSpec(Network, human_name="Network", short_description="The gap-filled network")
    }

    config_specs = {
        'tax_id':
        StrParam(
            default_value='', human_name="Taxonomy ID",
            short_description="The taxonomy id used to fill gaps"),
        'skip_cofactors':
        BoolParam(
            default_value=True, human_name="Skip cofactors",
            short_description="True to skip gaps related to dead-end cofactors. False otherwise"),
        'fill_each_gap_once':
        BoolParam(
            default_value=True, human_name="Fill each gap once",
            short_description="True to fill each gap with only one putative reaction. False otherwise"), }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = inputs["network"]

        i = 0
        nb_gaps_filled = 0
        max_gaps_filled = 0
        while True:
            i += 1
            done = max_gaps_filled-nb_gaps_filled
            if max_gaps_filled == 0:
                perc = 0
            else:
                perc = 100 * done/max_gaps_filled
            if perc < 0:
                perc = 0

            self.update_progress_value(perc, message=f"Doing pass {i} ...")

            nb_gaps_filled = self._fill_gaps_with_tax(net, params)
            message = f"Pass {i} done: {nb_gaps_filled} gap(s) filled."
            self.update_progress_value(perc, message=message)
            if nb_gaps_filled == 0:
                break
            max_gaps_filled = max(max_gaps_filled, nb_gaps_filled)

        return {"network": net}

    def _fill_gaps_with_tax(self, net, params):
        nb_gaps_filled = 0
        helper = GapFinderHelper()
        helper.attach_task(self)
        dead_end_list = helper.find_deadend_compound_ids(net)
        if len(dead_end_list) == 0:
            self.log_info_message('No dead-end metabolites exist anymore')
            return nb_gaps_filled

        tax_id = params["tax_id"]
        skip_cofactors = params["skip_cofactors"]
        # fill_each_gap_once = params["fill_each_gap_once"]
        self.log_info_message(f'Number of dead-end metabolites: {len(dead_end_list)}')

        if tax_id:
            tax = BiotaTaxo.get_or_none(BiotaTaxo.tax_id == tax_id)
            if tax is None:
                raise BadRequestException(f"No taxonomy found with taxonomy id {tax_id}")
        else:
            tax = None

        for k in dead_end_list:
            list_fo_rxns = []
            comp: Compound = net.compounds[k]

            if comp.is_sink():
                raise BadRequestException("Coherence check. A sink reaction compound should not be a gap compound.")
            if not comp.is_steady():
                continue
            if comp.is_cofactor() and skip_cofactors:
                continue
            if not comp.chebi_id:
                continue

            biota_c_list = BiotaCompound.search_by_chebi_ids(comp.chebi_id)

            if len(biota_c_list) == 0:
                Logger.warning(f'No compound corresponds to chebi_id "{comp.chebi_id}" in biota db')
                net.set_compound_recon_tag(comp.id, {
                    "id": comp.id,
                    "is_chebi_not_found": True,
                    "error": "CheBI ID not found"
                })

            reaction_enzyme_cls = BiotaReaction.enzymes.get_through_model()
            for biota_c in biota_c_list:
                if tax is None:
                    for biota_rxn in biota_c.reactions:
                        enzymes = BiotaEnzyme.select(BiotaEnzyme.id) \
                            .join(reaction_enzyme_cls, on=(reaction_enzyme_cls.enzyme == BiotaEnzyme.id)) \
                            .where(reaction_enzyme_cls.reaction == biota_rxn)\
                            .where(getattr(BiotaEnzyme, "tax_"+tax.rank) == tax.tax_id)

                        if len(enzymes):
                            rxns = Reaction.from_biota(biota_reaction=biota_rxn)
                            list_fo_rxns.extend(rxns)
                else:
                    for biota_rxn in biota_c.reactions:
                        rxns = Reaction.from_biota(biota_reaction=biota_rxn)
                        list_fo_rxns.extend(rxns)

            # for rxn in rxns:
            #     # if rxn.i
            #     if not net.reaction_exists(rxn):  # an existing reaction may be given by biota
            #         net.add_reaction(rxn)
            #         net.set_reaction_recon_tag(rxn.id, {
            #             "id": rxn.id,
            #             "is_from_gap_filling": True
            #         })
            #         nb_gaps_filled += 1
            #         is_filled_once = True
            #         break  # > select only one reaction

        return nb_gaps_filled
