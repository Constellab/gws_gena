
import pandas as pd

from gws_core import (ConfigParams, InputSpec,
                      InputSpecs, ListParam, OutputSpec, OutputSpecs,
                      StrParam, Table, Task, TaskInputs,
                      TaskOutputs, TypingStyle, task_decorator)
from gws_gena.twin.twin_v2 import TwinV2

@task_decorator("KOACobra", human_name="KOA Cobra", short_description="Knock out Analysis by Cobra Toolbox",
                style=TypingStyle.community_icon(icon_technical_name="delete_forever", background_color="#d9d9d9"))
class KOACobra(Task):
    """
    KOA Cobra task class

    """

    input_specs = InputSpecs({'twin': InputSpec(TwinV2, human_name="Digital twin",
                             short_description="The digital twin to analyze")})
    output_specs = OutputSpecs({
        'koa_result': OutputSpec(Table, human_name="KOA result table", short_description="The KOA result tables")
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
            human_name="Fluxes to minimize", short_description="The fluxes to minimize"),
        "reaction_to_knock_out":
        StrParam(
            default_value=None, optional=False,
            human_name="Reaction to knock out", short_description="The reaction to knock out")
        }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        twin: TwinV2 = inputs["twin"]
        fluxes_to_maximize = params["fluxes_to_maximize"]
        reaction_to_knock_out = params["reaction_to_knock_out"]

        network = twin.get_network()
        model = network.get_cobra_model()

        if fluxes_to_maximize :
            model.objective = fluxes_to_maximize

        with model:
            getattr(model.reactions, reaction_to_knock_out).knock_out()
            koa = model.optimize()
            
        koa_result = Table(koa.to_frame())

        return {
            'koa_result': koa_result
        }
