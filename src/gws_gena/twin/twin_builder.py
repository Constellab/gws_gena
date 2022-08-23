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
        'context': InputSpec(Context, human_name="Context", short_description="The metabolic context", is_skippable=True)
    }
    output_specs = {
        'twin': OutputSpec(Twin, human_name="Digital twin", short_description="The digital twin"),
    }

    config_specs = {"use_context": BoolParam(
        default_value=True, human_name="Use context", short_description="Set True to use the context, False otherwise."), }

    def check_before_run(self, params: ConfigParams, inputs: TaskInputs) -> CheckBeforeTaskResult:
        if params["use_context"]:
            if not inputs.get("context"):
                return {"result": False, "message": "No context given"}
        return {"result": True, "message": None}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = inputs["network"]
        twin = Twin()
        twin.add_network(net)
        if params["use_context"]:
            ctx = inputs["context"]
            twin.add_context(ctx, related_network=net)
        return {"twin": twin}
