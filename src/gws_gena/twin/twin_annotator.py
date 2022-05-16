# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, InputSpec, OutputSpec, Task, TaskInputs,
                      TaskOutputs, task_decorator)

from ..fba.fba_result import FBAResult
from .helper.twin_annotator_helper import TwinAnnotatorHelper
from .twin import Twin

# ####################################################################
#
# TwinAnnotator class
#
# ####################################################################


@task_decorator("TwinAnnotator", human_name="Twin annotator",
                short_description="Annotate a digital twin with estimated fluxes")
class TwinAnnotator(Task):
    input_specs = {
        'twin': InputSpec(Twin, human_name="Digital twin", short_description="The digital twin to annotate"),
        'fba_result': InputSpec(FBAResult, human_name="FBA result", short_description="The FBA result"),
    }
    output_specs = {'twin': OutputSpec(Twin, human_name="Digital twin", short_description="The annotated digital twin")}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        twin = inputs["twin"]
        fba_result = inputs["fba_result"]
        TwinAnnotatorHelper.annotate(twin, fba_result)
        return {"twin": twin}
