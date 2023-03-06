# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, InputSpec, OutputSpec, StringHelper,
                      StrParam, Task, TaskInputs, TaskOutputs, task_decorator)

from ..data.medium_table import MediumTable
from ..network.network import Network
from ..recon.helper.recon_helper import ReconHelper


@task_decorator("TransporterAdder", human_name="Transporter adder", short_description="Transporter adder")
class TransporterAdder(Task):
    """
    Transporter adder task.
    """

    input_specs = {
        'network': InputSpec(Network, human_name="The network"),
        'medium_table': InputSpec(MediumTable, human_name="Medium table")
    }
    output_specs = {'network': OutputSpec(Network)}
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        helper = ReconHelper()
        helper.attach_task(self)

        net = inputs['network']
        medium_table = inputs['medium_table']

        helper.add_medium_to_network(net, medium_table)

        return {"network": net}
