# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BadRequestException, ConfigParams, InputSpec, ListParam,
                      OutputSpec, StrParam, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ...data.ec_table import ECTable
from ...data.entity_id_table import EntityIDTable
from ...fba.fba import FBA
from ...twin.twin import Twin
from .dep_koa_result_table import KOAResultTable


@task_decorator("KOA_001", human_name="KOA", short_description="KnockOut Analysis")
class KOA(Task):
    """
    KOA class.

    This task is deprecated and deactivated
    """

    input_specs = {
        'twin': InputSpec(Twin, human_name="Digital twin", short_description="The digital twin to analyze"),
        'ko_table': InputSpec([EntityIDTable, ECTable], human_name="KO table", short_description="The table of KO hypotheses"),
    }
    output_specs = {'result': OutputSpec(KOAResultTable, human_name="KOA result table",
                                         short_description="The result table of KOA")}
    config_specs = {
        **FBA.config_specs,
        'monitored_fluxes':
        ListParam(
            optional=True, human_name="Monitored fluxes", visibility=ListParam.PROTECTED_VISIBILITY,
            short_description="The list of fluxes to monitor. By default, all the reactions are monitored. Set 'biomass' to only monitor the biomass reaction flux."),
        'ko_delimiter':
        StrParam(
            default_value=",", human_name="Multiple KO delimiter",
            short_description="The delimiter used to separate IDs or EC numbers when multiple KO are performed")}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        raise BadRequestException("This task is deprecated and deactivated.")
