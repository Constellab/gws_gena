
from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, Task, TaskInputs, TaskOutputs, ConfigSpecs,
                      task_decorator)

from .flat_twin import FlatTwin
from .twin import Twin


@task_decorator("TwinFlattener", human_name="Twin flattener",
                short_description="Flatten a digital twin of cell metabolism", hide=True)
class TwinFlattener(Task):
    """ TwinFlattener

    Flatten a digital twin of cell metabolism
    """

    input_specs = InputSpecs({
        'twin': InputSpec(Twin, human_name="Digital twin", short_description="The digital twin to flatten"),
    })
    output_specs = OutputSpecs({'flat_twin': OutputSpec(
        FlatTwin, human_name="Flat digital twin", short_description="The flat digital twin")})

    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        twin = inputs["twin"]
        return {"flat_twin": twin.flatten()}
