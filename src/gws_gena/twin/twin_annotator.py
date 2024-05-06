
from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, Task, TaskInputs, TaskOutputs, TypingStyle,
                      task_decorator)

from ..fba.fba_result import FBAResult
from ..fva.fva_result import FVAResult
from ..koa.koa_result import KOAResult
from .helper.twin_annotator_helper import TwinAnnotatorHelper
from .twin import Twin

# ####################################################################
#
# TwinAnnotator class
#
# ####################################################################


@task_decorator("TwinAnnotator", human_name="Twin annotator",
                short_description="Annotate a digital twin of cell metabolism with estimated metabolic fluxes",
                style=TypingStyle.material_icon(material_icon_name="auto_fix_high", background_color="#d9d9d9"))
class TwinAnnotator(Task):
    """ TwinAnnotator

    Annotate a digital twin of cell metabolism with estimated metabolic fluxes from a FBA, a FVA or a KOA.
    """

    input_specs = InputSpecs({
        'twin':
        OutputSpec(
            Twin, human_name="Simulated digital twin",
            short_description="The simulated digital twin"),
        'metabolic_fluxes':
        InputSpec(
            (FBAResult, FVAResult, KOAResult),
            human_name="Estimated metabolic fluxes",
            short_description="The FBA, FVA or KOA result")})
    output_specs = OutputSpecs({'twin': OutputSpec(Twin, human_name="Digital twin",
                               short_description="The annotated digital twin")})

    def run(self, _: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        metabolic_fluxes = inputs['metabolic_fluxes']
        twin = inputs["twin"]
        helper = TwinAnnotatorHelper()
        helper.attach_message_dispatcher(self.message_dispatcher)
        if isinstance(metabolic_fluxes, FVAResult):
            helper.annotate_from_fva_result(twin=twin, simulation=None, fva_result=metabolic_fluxes)
        elif isinstance(metabolic_fluxes, FBAResult):
            helper.annotate_from_fba_result(twin=twin, simulation=None, fba_result=metabolic_fluxes)
        elif isinstance(metabolic_fluxes, KOAResult):
            helper.annotate_from_koa_result(twin=twin, koa_result=metabolic_fluxes)

        return {"twin": twin}
