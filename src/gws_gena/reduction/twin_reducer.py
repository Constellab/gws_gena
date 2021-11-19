# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs
from ..twin.twin import Twin, FlatTwin

@task_decorator("TwinReducer")
class TwinReducer(Task):
    input_specs = { 'twin': (Twin, FlatTwin), }
    output_specs = { 'twin': (Twin,) }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        twin = inputs["twin"]
        fba_result = inputs["fba_result"]
        annotated_bio: Twin = TwinAnnotatorHelper.annotate(twin, fba_result)
        return { "twin": annotated_bio }