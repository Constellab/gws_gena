# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import math

from gws_core import (ConfigParams, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ..fba.fba_result import FBAResult
from .helper.twin_annotator_helper import TwinAnnotatorHelper
from .twin import Twin

# ####################################################################
#
# TwinAnnotator class
#
# ####################################################################


@task_decorator("TwinAnnotator", human_name="Twin annotator", short_description="Annotate a twin using a FBA result")
class TwinAnnotator(Task):
    input_specs = {'twin': (Twin,), 'fba_result': (FBAResult,)}
    output_specs = {'twin': (Twin,)}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        twin = inputs["twin"]
        fba_result = inputs["fba_result"]
        annotated_bio: Twin = TwinAnnotatorHelper.annotate(twin, fba_result)
        return {"twin": annotated_bio}
