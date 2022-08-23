# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, InputSpec, OutputSpec, Task, TaskInputs,
                      TaskOutputs, task_decorator)

from .flat_twin import FlatTwin
from .twin import Twin


@task_decorator("TwinFlattener", human_name="Twin flattener",
                short_description="Flatten a digital twin of cell metabolism")
class TwinFlattener(Task):
    """ TwinFlattener

    Flatten a digital twin of cell metabolism
    """
    
    input_specs = {
        'twin': InputSpec(Twin, human_name="Digital twin", short_description="The digital twin to flatten"),
    }
    output_specs = {'flat_twin': OutputSpec(
        FlatTwin, human_name="Flat digital twin", short_description="The flat digital twin"), }

    config_specs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        twin = inputs["twin"]
        return {"flat_twin": twin.flatten()}
