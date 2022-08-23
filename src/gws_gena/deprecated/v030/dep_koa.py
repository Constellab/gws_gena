# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BadRequestException, BoolParam, ConfigParams, InputSpec,
                      ListParam, OutputSpec, StrParam, Task, TaskInputs,
                      TaskOutputs, task_decorator)

from ...data.ec_table import ECTable
from ...data.entity_id_table import EntityIDTable
from ...twin.twin import Twin
from ..v031.dep_koa_result_table import KOAResultTable
from .dep_fba import FBA


@task_decorator("KOA", human_name="KOA", short_description="Depreacted KnockOut Analysis",
                hide=True, deprecated_since='0.3.1', deprecated_message="Use new version of KOA")
class KOA(Task):
    """
    KOA class.
    """

    input_specs = {
        'twin': InputSpec(Twin),
        'ko_table': InputSpec([EntityIDTable, ECTable]),
    }
    output_specs = {'result': OutputSpec(KOAResultTable)}
    config_specs = {
        **FBA.config_specs,
        'monitored_fluxes': ListParam(optional=True, short_description="The list of fluxes to monitor"),
        'ko_delimiter':
        StrParam(
            default_value=",",
            short_description="The delimiter used to separate IDs or EC numbers when multiple KO are performed")}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        raise BadRequestException("This task is deprecated and deactivated.")
