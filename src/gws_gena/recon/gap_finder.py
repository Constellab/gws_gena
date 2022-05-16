# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, InputSpec, OutputSpec, Task, TaskInputs,
                      TaskOutputs, task_decorator)

from ..network.network import Network
from .gap_finder_result import GapFinderResult


@task_decorator("GapFinder", human_name="Gap finder",
                short_description="Find all the gaps (related to dead-end metabolites) in a network")
class GapFinder(Task):
    """
    GapFinder class.
    """

    input_specs = {
        'network': InputSpec(Network, human_name="Network", short_description="Network to search in"),
    }

    output_specs = {'result': OutputSpec(GapFinderResult, human_name="Gap finder result",
                                         short_description="The resul of Gap finder"), }

    config_specs = {}

    async def run(self, _: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = inputs["network"]
        gaps = net.get_gaps()
        result = GapFinderResult(gaps=gaps)
        return {"result": result}