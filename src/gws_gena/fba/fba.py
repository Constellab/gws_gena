# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BoolParam, ConfigParams, InputSpec, ListParam,
                      OutputSpec, StrParam, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ..twin.twin import Twin
from .fba_helper.fba_helper import FBAHelper
from .fba_result import FBAResult


@task_decorator("FBA_001", human_name="FBA", short_description="Flux balance Analysis")
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
        twin = inputs["twin"]
        solver = params["solver"]
        fluxes_to_maximize = params["fluxes_to_maximize"]
        fluxes_to_minimize = params["fluxes_to_minimize"]
        fill_gaps_with_sinks = params["fill_gaps_with_sinks"]
        ignore_cofactors = params["ignore_cofactors"]
        relax_qssa = params["relax_qssa"]

        helper = FBAHelper()
        helper.attach(self)
        fba_result: FBAResult = helper.run(
            twin, solver, fluxes_to_maximize, fluxes_to_minimize, fill_gaps_with_sinks=fill_gaps_with_sinks,
            ignore_cofactors=ignore_cofactors, relax_qssa=relax_qssa)

        return {"result": fba_result}

    # -- B --
