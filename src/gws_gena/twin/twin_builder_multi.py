# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ..context.context import Context
from ..network.network import Network
from .twin import Twin

# ####################################################################
#
# Twin class
#
# ####################################################################


@task_decorator("TwinBuilderMulti", human_name="Twin builder multi",
                short_description="Build a digital twin of cell metabolism using a metabolic network and a context")
class TwinBuilderMulti(Task):
    """ TwinBuilderMulti

    Build a digital twin of cell metabolism using a metabolic network and a context
    """

    input_specs = InputSpecs({
        'network': InputSpec(Network, human_name="Network", short_description="The metabolic network"),
        'context': InputSpec(Context, human_name="Context", short_description="The metabolic context", is_optional=True)
    })
    output_specs = OutputSpecs({
        'twin': OutputSpec(Twin, human_name="Digital twin", short_description="The digital twin"),
    })

    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = inputs["network"]
        twin = Twin()
        twin.add_network(net)
        if inputs.get("context") is not None:
            ctx = inputs["context"]
            twin.add_context(ctx, related_network=net)
        else:
            twin.add_context(Context(), related_network=net)
        return {"twin": twin}
