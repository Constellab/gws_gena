# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BoolParam, ConfigParams, InputSpec, OutputSpec, Task,
                      TaskInputs, TaskOutputs, task_decorator)

from ....data.ec_table import ECTable
from ....data.entity_id_table import EntityIDTable
from ...network import Network
from ..helper.reaction_remover_helper import ReactionRemoverHelper


@task_decorator("ReactionRemover", human_name="Reaction remover",
                short_description="Remove a list of reactions from a network")
class ReactionRemover(Task):

    input_specs = {
        'network': InputSpec(Network, human_name="Network", short_description="Network to trim"),
        'reaction_table': InputSpec(
            (ECTable, EntityIDTable), human_name="Table of EC numbers or IDs", short_description="The table of reactions to remove"),
    }
    output_specs = {
        'network': OutputSpec(Network, human_name="Network", short_description="The network after trimming")
    }
    config_specs = {
        "reverse_remove":
        BoolParam(
            default_value=False, visibility="protected",
            short_description="Set True to remove the reactions not given in the input list. By default, ")}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        network: Network = inputs["network"]
        reaction_table = inputs["reaction_table"]
        reverse_remove = params["reverse_remove"]
        helper = ReactionRemoverHelper()
        helper.attach_task(self)
        helper.remove_list_of_reactions(
            network, reaction_table, reverse_remove=reverse_remove)
        return {"network": network}
