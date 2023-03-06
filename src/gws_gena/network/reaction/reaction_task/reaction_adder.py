# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, InputSpec, OutputSpec, StrParam, Task,
                      TaskInputs, TaskOutputs, task_decorator)

from ....data.ec_table import ECTable
from ....data.entity_id_table import EntityIDTable
from ...network import Network
from ..helper.reaction_adder_helper import ReactionAdderHelper


@task_decorator("ReactionAdder", human_name="Reaction adder", short_description="Add a list of reactions to a network")
class ReactionAdder(Task):
    """
    ReactionAdder class.

    Add a list of reactions to an existing network
    """

    input_specs = {
        'network': InputSpec(Network, human_name="Network", short_description="Network to complete"),
        'reaction_table': InputSpec(
            (ECTable, EntityIDTable), human_name="Table of EC numbers or IDs", short_description="The table of reactions to add"),
    }
    output_specs = {
        'network': OutputSpec(Network, human_name="Network", short_description="The network after completion"),
    }
    config_specs = {
        'tax_id': StrParam(
            default_value='', human_name="Taxonomy ID", short_description="The NCBI taxonomy id"),
        'tax_search_method':
        StrParam(
            default_value='bottom_up', human_name="Taxonomy search method",
            short_description="If 'bottom_up', the algorithm will to traverse the taxonomy tree to search in the higher taxonomy levels until a reaction is found. If 'none', the algorithm will only search at the given taxonomy level given by `tax_id`")
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        network: Network = inputs["network"]
        tax_id = params['tax_id']
        tax_search_method = params['tax_search_method']
        reaction_table = inputs["reaction_table"]

        helper = ReactionAdderHelper()
        helper.attach_task(self)
        helper.add_reactions(
            network, reaction_table, tax_id, tax_search_method=tax_search_method)

        return {"network": network}
