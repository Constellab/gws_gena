# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (Task, task_decorator, ConfigParams, 
                        TaskInputs, TaskOutputs, BoolParam, 
                        SkippableIn, CheckBeforeTaskResult)
from ..network.network import Network
from .twin import Twin
from .twin_context import TwinContext

# ####################################################################
#
# Twin class
#
# ####################################################################

@task_decorator("TwinBuilder")
class TwinBuilder(Task):
    input_specs = { 'network': (Network,), 'context': SkippableIn(TwinContext) }
    output_specs = { 'twin': (Twin,) }
    config_specs = {
        "use_context": BoolParam(default_value=True, human_name="Use context", short_description="Set True to use the context, False otherwise."),
    }
    
    def check_before_run(self, params: ConfigParams, inputs: TaskInputs) -> CheckBeforeTaskResult:
        if params["use_context"]:
            if not inputs.get("context"):
                return {"result": False, "message": None}
        return {"result": True, "message": None}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = inputs["network"]
        twin = Twin()
        twin.add_network(net)
        if params["use_context"]:
            ctx = inputs["context"]
            twin.add_context(ctx, related_network=net)
        return {"twin" : twin}
