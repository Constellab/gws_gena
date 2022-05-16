# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BadRequestException, Logger

from ...network.compound import Compound
from ...network.reaction import Reaction


class SinkHelper:

    @staticmethod
    #def fill_gaps_with_sinks(net, biomass_and_medium_gaps_only=False) -> int:
    def fill_gaps_with_sinks(net) -> int:
        """ Fill gaps with sink reactions """
        gap_info = net.get_gaps()
        nb_filled = 0
        for k in gap_info["compounds"]:
            is_dead_end = gap_info["compounds"][k]["is_dead_end"]
            if is_dead_end:
                comp: Compound = net.compounds[k]
                if comp.is_sink():
                    raise BadRequestException("A sink reaction compound cannot not be a gap compound.")
                # if biomass_and_medium_gaps_only:
                #     is_in_biomass_or_medium = net.get_compound_recon_tag(comp.id, "is_in_biomass_or_medium")
                #     if not is_in_biomass_or_medium:
                #         # skip this compound
                #         continue
                rxn = Reaction.create_sink_reaction(related_compound=comp)
                net.set_reaction_recon_tag(rxn.id, {
                    "id": rxn.id,
                    "is_from_gap_filling": True
                })
                nb_filled += 1

        if nb_filled:
            Logger.progress(f"A total of {nb_filled} gaps filled with sink reactions")
        else:
            Logger.progress("OK: No gap filled with sink reactions")

        return nb_filled
