# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, StrParam, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ...data.ec_table import ECTable
from ...data.id_table import IDTable
from ...network.network import Network, Reaction
from ..network_helper.reaction_adder_helper import ReactionAdderHelper


@task_decorator("ReactionAdder")
class ReactionAdder(Task):
    """
    ReactionAdder class.

    Add a list of reactions to an existing network
    """

    input_specs = {'network': (Network,), 'reaction_table': (ECTable, IDTable,), }
    output_specs = {'network': (Network,)}
    config_specs = {
        'tax_id': StrParam(
            default_value='', human_name="Taxonomy ID", short_description="The NCBI taxonomy id"),
        'tax_search_method':
        StrParam(
            default_value='bottom_up', human_name="Taxonomy search method",
            short_description="If 'bottom_up', the algorithm will to traverse the taxonomy tree to search in the higher taxonomy levels until a reaction is found. If 'none', the algorithm will only search at the given taxonomy level given by `tax_id`")
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        network: Network = inputs["network"]
        tax_id = params['tax_id']
        tax_search_method = params['tax_search_method']
        reaction_table = inputs["reaction_table"]

        new_network: Network = ReactionAdderHelper.add_list_of_reactions(
            network, reaction_table, tax_id, tax_search_method=tax_search_method)

        return {"network": new_network}