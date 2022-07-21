# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BoolParam, ConfigParams, FloatParam, InputSpec,
                      ListParam, OutputSpec, StrParam, Task, TaskInputs,
                      TaskOutputs, task_decorator)

from ..twin.twin import Twin
from .fba_helper.fba_helper import FBAHelper
from .fba_result import FBAResult


@task_decorator("FBA_002", human_name="FBA", short_description="Flux balance analysis")
class FBA(Task):
    """
    FBA task class

    Performs Flux Balance Analysis from a digital twin.

    A digital twin is a mathematical representation of the metabolic interactions involved in a living cell or microbial organism
    (e.g. animal cell, bacteria, fungus, etc.).
    """

    input_specs = {'twin': InputSpec(Twin, human_name="Digital twin", short_description="The digital twin to analyze")}
    output_specs = {'result': OutputSpec(FBAResult, human_name="FBA result", short_description="The FBA result")}
    config_specs = {
        "biomass_optimization": StrParam(allowed_values=["", "maximize", "minimize"], default_value="", human_name="Biomass optimization", short_description="Biomass optimization"),
        "fluxes_to_maximize": ListParam(default_value="[]", visibility=StrParam.PROTECTED_VISIBILITY, human_name="Fluxes to maximize", short_description="The fluxes to maximize"),
        "fluxes_to_minimize": ListParam(default_value="[]", visibility=StrParam.PROTECTED_VISIBILITY, human_name="Fluxes to minimize", short_description="The fluxes to minimize"),
        "solver": StrParam(default_value="quad", visibility=StrParam.PROTECTED_VISIBILITY, allowed_values=["highs-ds", "highs-ipm", "highs", "interior-point", "quad"], human_name="Solver", short_description="The optimization solver"),
        "relax_qssa": BoolParam(default_value=False, visibility=StrParam.PROTECTED_VISIBILITY, human_name="Relax QSSA", short_description="True to relaxing the quasi-steady state assumption (QSSA) constrain (quad solver is used). False otherwise."),
        "qssa_relaxation_strength": FloatParam(default_value=1, min_value=1, visibility=StrParam.PROTECTED_VISIBILITY, human_name="QSSA relaxation", short_description="Used only if QSSA is relaxed. The higher it is, the stronger is the QSSA. Hint: Set to the number of reactions to have strong QSSA contrain."),
        "fill_gaps_with_sinks": BoolParam(default_value=False, visibility=StrParam.PROTECTED_VISIBILITY, human_name="Fill gaps with sinks", short_description="True to fill gaps using sink reaction. False otherwise"),
        "ignore_cofactors": BoolParam(default_value=False, visibility=StrParam.PROTECTED_VISIBILITY, human_name="Ignore cofactors", short_description="True to ignore cofactors quasi-steady state for cofactors. False otherwise.")
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        twin = inputs["twin"]
        solver = params["solver"]
        biomass_optimization = params["biomass_optimization"]
        fluxes_to_maximize = params["fluxes_to_maximize"]
        fluxes_to_minimize = params["fluxes_to_minimize"]
        fill_gaps_with_sinks = params["fill_gaps_with_sinks"]
        ignore_cofactors = params["ignore_cofactors"]
        relax_qssa = params["relax_qssa"]
        qssa_relaxation_strength = params["qssa_relaxation_strength"]

        helper = FBAHelper()
        helper.attach(self)
        fba_result: FBAResult = helper.run(
            twin, solver, fluxes_to_maximize, fluxes_to_minimize, biomass_optimization=biomass_optimization,
            fill_gaps_with_sinks=fill_gaps_with_sinks, ignore_cofactors=ignore_cofactors, relax_qssa=relax_qssa,
            qssa_relaxation_strength=qssa_relaxation_strength)

        return {"result": fba_result}

    # -- B --
