# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BoolParam, CheckBeforeTaskResult, ConfigParams,
                      InputSpec, OutputSpec, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ..context.context import Context
from ..network.network import Network
from .twin import Twin

# ####################################################################
#
# Twin class
#
# ####################################################################


@task_decorator("TwinBuilder", human_name="Twin builder",
                short_description="Build a digital twin of cell metabolism using a metabolic network and a context")
class TwinBuilder(Task):
    """ TwinBuilder

    Build a digital twin of cell metabolism using a metabolic network and a context
    """

    input_specs = {
        'network': InputSpec(Network, human_name="Network", short_description="The metabolic network"),
        'context': InputSpec(Context, human_name="Context", short_description="The metabolic context", is_optional=True)
    }
    output_specs = {
        'twin': OutputSpec(Twin, human_name="Digital twin", short_description="The digital twin"),
    }

    config_specs = {}

    def check_before_run(self, params: ConfigParams, inputs: TaskInputs) -> CheckBeforeTaskResult:
        if params["use_context"]:
            if not inputs.get("context"):
                return {"result": False, "message": "No context given"}
        return {"result": True, "message": None}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = inputs["network"]
        twin = Twin()
        twin.add_network(net)
        if inputs.get("use_context") is not None:
            ctx = inputs["context"]
            twin.add_context(ctx, related_network=net)
        else:
            twin.add_context(Context(), related_network=net)
        return {"twin": twin}
