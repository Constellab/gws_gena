# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import math

from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs
from .twin import Twin
from ..fba.fba_result import FBAResult
from ..helper.twin_annotator_helper import TwinAnnotatorHelper

# ####################################################################
#
# MetaTwinAnnotator class
#
# ####################################################################

@task_decorator("MetaTwinAnnotator")
class MetaTwinAnnotator(Task):
    input_specs = { 'twin': (Twin,), 'fba_result': (FBAResult,) }
    output_specs = { 'twin': (Twin,) }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        twin = inputs["twin"]
        fba_result = inputs["fba_result"]
        annotated_bio: Twin = TwinAnnotatorHelper.annotate(twin, fba_result)
        return { "twin": annotated_bio }
