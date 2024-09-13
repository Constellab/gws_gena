
import pandas as pd

from gws_core import (ConfigParams, InputSpec,
                      InputSpecs, ListParam, OutputSpec, OutputSpecs,
                      StrParam, Table, Task, TaskInputs,
                      TaskOutputs, TypingStyle, task_decorator)
from gws_gena.twin.twin_v2 import TwinV2

@task_decorator("FBACobra", human_name="FBA Cobra", short_description="Flux balance analysis by Cobra Toolbox",
                style=TypingStyle.community_icon(icon_technical_name="cone", background_color="#d9d9d9"))
class FBACobra(Task):
    """
    FBA task class

    Performs Flux Balance Analysis from a digital twin.

    A digital twin is a mathematical representation of the metabolic interactions involved in a living cell or microbial organism
    (e.g. animal cell, bacteria, fungus, etc.).

    You need to provide your twin in the input and you can set some parameters. The most important is to choose whether you want to maximize or minimize the biomass flux.
    Then, you can add other fluxes to optimize (fluxes to maximize and fluxes to minimize), the solver and some parameters related to the solver method.
    The last parameter "Number of simulations" allows you to run multiple simulations of FBA using your context with multi target values.

    In output you will get your twin annotated and two tables with the estimated fluxes.
    """

    input_specs = InputSpecs({'twin': InputSpec(TwinV2, human_name="Digital twin",
                             short_description="The digital twin to analyze")})
    output_specs = OutputSpecs({
        'fba_result': OutputSpec(Table, human_name="FBA result table", short_description="The FBA result tables"),
        'fluxes_maximised_result': OutputSpec(Table, human_name="Fluxes maximised result table", short_description="The fluxes maximised result table")
    })
    config_specs = {
        "biomass_optimization":
        StrParam(
            allowed_values=["", "maximize", "minimize"],
            default_value=None, optional=True, human_name="Biomass optimization",
            short_description="Biomass optimization"),
        "fluxes_to_maximize":
        ListParam(
            default_value=None, optional=True, visibility=StrParam.PROTECTED_VISIBILITY,
            human_name="Fluxes to maximize", short_description="The fluxes to maximize"),
        "fluxes_to_minimize":
        ListParam(
            default_value=None, optional=True, visibility=StrParam.PROTECTED_VISIBILITY,
            human_name="Fluxes to minimize", short_description="The fluxes to minimize")
        }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        twin: TwinV2 = inputs["twin"]
        fluxes_to_maximize = params["fluxes_to_maximize"]

        network = twin.get_network()
        model = network.get_cobra_model()

        if fluxes_to_maximize :
            model.objective = fluxes_to_maximize
            name_fluxes_to_maximize = fluxes_to_maximize
        else :
            name_fluxes_to_maximize = model.objective.expression
        fba = model.optimize()
        self.update_progress_value(100, message="Running FBA")
        fba_result = Table(fba.to_frame())

        #Table to store the value maximised
        objective_value = model.optimize().objective_value
        df_fluxes_maximised_result = pd.DataFrame({"value": [objective_value]}, index=[name_fluxes_to_maximize])
        fluxes_maximised_result = Table(df_fluxes_maximised_result)

        return {
            'fba_result': fba_result,
            'fluxes_maximised_result' : fluxes_maximised_result
        }
