# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BoolParam, ConfigParams, OptionalIn, Task, TaskInputs,
                      TaskOutputs, task_decorator)

from ...data.ec_table import ECTable
from ...data.id_table import IDTable
from ...network.network import Network
from ..network_helper.reaction_remover_helper import ReactionRemoverHelper


@task_decorator("ReactionRemover")
class ReactionRemover(Task):

    input_specs = {'network': (Network,), 'reaction_table': (ECTable, IDTable,), }
    output_specs = {'network': (Network,)}
    config_specs = {
        "reverse_remove":
        BoolParam(
            default_value=False, visibility="protected",
            short_description="Set True to remove the reactions not given in the input list. By default, ")}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        network: Network = inputs["network"]
        reaction_table = inputs["reaction_table"]
        reverse_remove = params["reverse_remove"]
        new_network: Network = ReactionRemoverHelper.remove_list_of_reactions(
            network, reaction_table, reverse_remove=reverse_remove)
        return {"network": new_network}