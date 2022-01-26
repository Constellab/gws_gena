# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ..network import Network


@task_decorator("NetworkMerger", human_name="Network merger", short_description="Merge two networks")
class NetworkMerger(Task):
    """
    NetworkMerger class.

    This process merge two networks
    """

    input_specs = {'network_1': (Network,), 'network_2': (Network,)}
    output_specs = {'network': (Network,)}
    config_specs = {}

    async def run(self, _: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net_1 = inputs['network_1'].copy()
        net_2 = inputs['network_2']
        for comp_id in net_2.compounds:
            cmp = net_2.compounds[comp_id]
            cmp.network = None

        for rxn_id in net_2.reactions:
            rxn = net_2.reactions[rxn_id]
            rxn.network = None
            try:
                net_1.add_reaction(rxn)
            except:
                pass

        return {'network': net_1}
