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
                short_description="Annotate a digital twin of cell metabolism with estimated metabolic fluxes")
class TwinAnnotator(Task):
    """ TwinAnnotator

    Annotate a digital twin of cell metabolism with estimated metabolic fluxes
    """

    input_specs = {'fba_result': InputSpec(FBAResult, human_name="FBA result", short_description="The FBA result")}
    output_specs = {'twin': OutputSpec(Twin, human_name="Digital twin", short_description="The annotated digital twin")}

    async def run(self, _: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        fba_result = inputs["fba_result"]
        twin = fba_result.get_twin().copy()
        helper = TwinAnnotatorHelper()
        helper.attach_task(self)
        helper.annotate_from_fba_result(twin, fba_result)
        return {"twin": twin}
