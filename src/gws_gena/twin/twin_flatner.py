# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs
from .twin import Twin
from .flat_twin import FlatTwin

@task_decorator("TwinFlattener")
class TwinFlattener(Task):
    input_specs = { 'twin': (Twin,), }
    output_specs = { 'flat_twin': (FlatTwin,) }
    config_specs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        twin = inputs["twin"]
        return {"flat_twin" : twin.flatten() }