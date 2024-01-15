# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, InputSpec, OutputSpec, Task, TaskInputs,
                      TaskOutputs, task_decorator)

from ..helper.network_merger import NetworkMergerHelper
from ..network import Network


@task_decorator("NetworkMerger", human_name="Network merger", short_description="Merge two networks")
class NetworkMerger(Task):
    """
    NetworkMerger class.

    This process merge two networks
    """

    input_specs = {
        'network_1': InputSpec(Network, human_name="Network 1", short_description="The first network"),
        'network_2': InputSpec(Network, human_name="Network 2", short_description="The second network"),
    }
    output_specs = {'network': OutputSpec(Network, human_name="Merged network",
                                          short_description="The merged network"), }
    config_specs = {}

    def run(self, _: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net1 = inputs['network_1']
        net2 = inputs['network_2']

        merger_helper = NetworkMergerHelper()
        merger_helper.attach_task(self)
        net = merger_helper.merge(destination_network=net1, source_network=net2)
        return {'network': net}
