# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...data.ec_table import ECTable
from ...data.entity_id_table import EntityIDTable
from ...network.network import Network, Reaction


class ReactionAdderHelper:

    @classmethod
    def add_list_of_reactions(cls, network: Network, reaction_table: (ECTable, EntityIDTable),
                              tax_id: str, tax_search_method: str = 'bottom_up', inplace=False) -> Network:
        if inplace:
            new_net = network
        else:
            new_net: Network = network.copy()
        if isinstance(reaction_table, ECTable):
            ec_list: list = reaction_table.get_ec_numbers()
            for ec in ec_list:
                try:
                    rxn = Reaction.from_biota(ec_number=ec, network=new_net, tax_id=tax_id,
                                              tax_search_method=tax_search_method)
                    new_net.add_reaction(rxn)
                except:
                    pass
        elif isinstance(reaction_table, EntityIDTable):
            id_list: list = reaction_table.get_ids()
            for rxn_id in id_list:
                try:
                    rxn = Reaction.from_biota(rhea_id=rxn_id, network=new_net)
                    new_net.add_reaction(rxn)
                except:
                    pass

        return new_net
