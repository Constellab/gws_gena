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

from ..network.compound import Compound
from ..network.graph import Graph
from ..network.network import Network
from ..network.reaction import Reaction
from .helper.gap_finder_helper import GapFinderHelper


@task_decorator("GapFiller2_001", human_name="Gap filler", short_description="Fills gaps in a networks")
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
        tax_id = params.get("tax_id")
        unicell = BiotaUnicellService.create_unicell(tax_id=tax_id)
        graph = Graph(net)
