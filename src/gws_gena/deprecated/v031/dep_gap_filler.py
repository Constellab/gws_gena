# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BadRequestException, BoolParam, ConfigParams, InputSpec,
                      OutputSpec, StrParam, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ...network.network import Network


@task_decorator("GapFiller", human_name="Gap filler", short_description="Fills gaps in a networks",
                hide=True, deprecated_since='0.3.2', deprecated_message="Use current GapFiller")
class GapFiller(Task):
    """
    GapFiller class.

    This task is no longer maintained
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
        'biomass_and_medium_gaps_only':
        BoolParam(
            default_value=False, human_name="Only biomass and medium gaps",
            short_description="True to only fill gaps related to compounds comming from the biomass equation or the medium composition; False otherwise."),
        'add_sink_reactions':
        BoolParam(
            default_value=False, human_name="Add sink reactions",
            short_description="True to add sink reactions to unresolved dead-end compounds. False otherwise"),
        'skip_cofactors':
        BoolParam(
            default_value=True, human_name="Skip cofactors",
            short_description="True to skip gaps related to dead-end cofactors. False otherwise"),
        'fill_each_gap_once':
        BoolParam(
            default_value=False, human_name="Fill each gap once",
            short_description="True to fill each gap with only one putative reaction. False otherwise"), }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        raise BadRequestException("This task is deprecated and deactivated.")
