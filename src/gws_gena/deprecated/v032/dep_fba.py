# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BadRequestException, BoolParam, ConfigParams, InputSpec,
                      ListParam, OutputSpec, StrParam, Task, TaskInputs,
                      TaskOutputs, task_decorator)

from ...fba.fba_result import FBAResult
from ...twin.twin import Twin


@task_decorator("FBA_001", human_name="Deprecated FBA", short_description="Flux balance analysis",
                hide=True, deprecated_since='0.4.0', deprecated_message="Use new version of FBA")
class FBA(Task):
    """
    FBA task class
    """

    input_specs = {'twin': InputSpec(Twin, human_name="Digital twin", short_description="The digital twin to analyze")}
    output_specs = {'result': OutputSpec(FBAResult, human_name="FBA result", short_description="The FBA result")}
    config_specs = {
        "fluxes_to_maximize": ListParam(default_value="[]", human_name="Fluxes to maximize", short_description="The fluxes to maximize"),
        "fluxes_to_minimize": ListParam(default_value="[]", visibility=StrParam.PROTECTED_VISIBILITY, human_name="Fluxes to minimize", short_description="The fluxes to minimize"),
        "solver": StrParam(default_value="quad", visibility=StrParam.PROTECTED_VISIBILITY, allowed_values=["highs-ds", "highs-ipm", "highs", "interior-point", "quad"], human_name="Solver", short_description="The optimization solver"),
        "relax_qssa": BoolParam(default_value=False, visibility=StrParam.PROTECTED_VISIBILITY, human_name="Relax QSSA", short_description="True to relaxing the quasi-steady state constrain (quad solver is used). False otherwise."),
        "fill_gaps_with_sinks": BoolParam(default_value=False, visibility=StrParam.PROTECTED_VISIBILITY, human_name="Fill gaps with sinks", short_description="True to fill gaps using sink reaction. False otherwise"),
        "ignore_cofactors": BoolParam(default_value=False, visibility=StrParam.PROTECTED_VISIBILITY, human_name="Ignore cofactors", short_description="True to ignore cofactors quasi-steady state for cofactors. False otherwise.")
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        raise BadRequestException("This task is deprecated and deactivated.")
