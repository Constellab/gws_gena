# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, OptionalIn, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ...data.ec_table import ECTable
from ...data.id_table import IDTable
from ...network.network import Network


@task_decorator("ReactionRemover")
class ReactionRemover(Task):

    input_specs = {'network': (Network,), 'reaction_table': (ECTable, IDTable,), }
    output_specs = {'network': (Network,)}
    config_specs = {}

    async def run(self, _: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net: Network = inputs["network"]
        new_net: Network = net.copy()
        table = inputs["reaction_table"]
        if isinstance(table, ECTable):
            ec_list: list = table.get_ec_numbers()
            for k, rxn in net.reactions.items():
                ec_number = rxn.enzyme.get("ec_number")
                if ec_number in ec_list:
                    new_net.remove_reaction(rxn.id)
        elif isinstance(table, IDTable):
            id_list: list = table.get_ids()
            for k, rxn in net.reactions.items():
                print(rxn.rhea_id)
                if rxn.rhea_id in id_list:
                    new_net.remove_reaction(rxn.id)
                elif k in id_list:
                    new_net.remove_reaction(rxn.id)

        return {"network": new_net}
