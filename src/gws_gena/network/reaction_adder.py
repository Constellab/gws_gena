# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import task_decorator, ConfigParams, Task, TaskOutputs, TaskInputs
from ..data.ec_number_table import ECNumberTable
from ..network.network import Network

@task_decorator("ReactionAdder")
class ReactionAdder(Task):
    """
    ReactionAdder class.
    
    Add a list of reactions to an existing network
    """
    
    input_specs = { 'network': (Network,), 'ec_number_table': (ECNumberTable,) }
    output_specs = { 'network': (Network,) }
    config_specs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        pass