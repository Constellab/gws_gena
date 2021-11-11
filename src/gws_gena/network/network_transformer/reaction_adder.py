# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, StrParam, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ...data.ec_table import ECTable
from ...data.id_table import IDTable
from ...network.network import Network, Reaction


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
        net: Network = inputs["network"]
        tax_id = params['tax_id']
        tax_search_method = params['tax_search_method']
        new_net: Network = net.copy()
        table = inputs["reaction_table"]
        if isinstance(table, ECTable):
            ec_list: list = table.get_ec_numbers()
            for ec in ec_list:
                try:
                    rxn = Reaction.from_biota(ec_number=ec, network=new_net, tax_id=tax_id,
                                              tax_search_method=tax_search_method)
                    new_net.add_reaction(rxn)
                except:
                    pass

        elif isinstance(table, IDTable):
            id_list: list = table.get_ids()
            print(id_list)
            for rxn_id in id_list:
                try:
                    rxn = Reaction.from_biota(rhea_id=rxn_id, network=new_net)
                    new_net.add_reaction(rxn)
                except:
                    pass

        return {"network": new_net}
