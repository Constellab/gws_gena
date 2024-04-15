
from gws_core import BadRequestException
from pandas import DataFrame

from ....helper.base_helper import BaseHelper
from ....network.compound.compound import Compound
from ....network.reaction.reaction import Reaction
from .gap_finder_helper import GapFinderHelper


class SinkHelper(BaseHelper):
    """ SinkHelper """

    def fill_gaps_with_sinks(self, net) -> int:
        """ Fill gaps with sink reactions """

        helper = GapFinderHelper()
        dead_end: DataFrame = helper.find_gaps(net)
        nb_filled = 0
        for k in dead_end.index:
            comp: Compound = net.compounds[k]
            if comp.is_sink():
                raise BadRequestException("A sink reaction compound cannot not be a gap compound.")
            rxn = Reaction.create_sink_reaction(related_compound=comp, network=net)
            net.update_reaction_recon_tag(rxn.id, {
                "id": rxn.id,
                "is_from_gap_filling": True
            })
            nb_filled += 1

        if nb_filled:
            self.log_info_message(f"{nb_filled} gaps filled with sink reactions")
        else:
            self.log_info_message("No gap filled with sink reactions")

        return nb_filled
