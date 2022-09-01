# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_biota import Compound as BiotaCompound
from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import Reaction as BiotaReaction
from gws_biota import Taxonomy as BiotaTaxo
from gws_biota import Unicell as BiotaUnicell
from gws_biota.unicell.unicell_service import \
    UnicellService as BiotaUnicellService
from gws_core import (BadRequestException, BoolParam, ConfigParams, InputSpec,
                      Logger, OutputSpec, StrParam, Task, TaskInputs,
                      TaskOutputs, task_decorator)

from ..network.compound.compound import Compound
from ..network.graph.graph import Graph
from ..network.network import Network
from ..network.reaction.reaction import Reaction
from .helper.gap_finder_helper import GapFinderHelper


@task_decorator("GapFiller", human_name="Fast gap filler", short_description="Fills gaps in a networks")
class GapFiller(Task):
    """
    GapFiller class.

    This process iteratively fills gaps related to dead-end compounds using the biota DB.
    A gap is detected if a steady compound is a dead-end compound.
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
            default_value=None, human_name="Taxonomy ID",
            short_description="The taxonomy id used to fill gaps")
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = inputs["network"]
        helper = GapFinderHelper()
        helper.attach_task(self)
        dead_ends = helper.find_deadend_compound_ids(net)
        if len(dead_ends) > 0:
            self.log_info_message(f"{len(dead_ends)} dead-end metabolites found")
            tax_id = params.get("tax_id")
            graph = Graph(net)
            added_edges = graph.gap_fill(tax_id=tax_id)
            added_rhea_ids = [edge["rhea_id"] for edge in added_edges]
            for rhea_id in added_rhea_ids:
                rxns = Reaction.from_biota(rhea_id=rhea_id)
                net.add_reaction(rxns[0])
                net.update_reaction_recon_tag(rxns[0].id, {"is_from_gap_fill": True})
        else:
            self.log_info_message("No dead-end metabolites found")

        return {'network': net}
