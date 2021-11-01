# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import task_decorator, ConfigParams, Task, TaskOutputs, TaskInputs
from ..data.ec_table import ECTable
from ..network.network import Network


@task_decorator("ReactionRemover")
class ReactionRemover(Task):
    
    input_specs = { 'network': (Network,), 'ec_table': (ECTable,) }
    output_specs = { 'network': (Network,) }
    config_specs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net: Network = inputs["network"]
        new_net: Network = net.copy()
        ec_table: ECTable = inputs["ec_table"]
        ec_list: list = ec_table.get_ec_numbers()
        for k, rxn in net.reactions.items():
            if rxn.enzyme in ec_list:
                new_net.remove_reaction(rxn)
        
        return { "network": new_net }