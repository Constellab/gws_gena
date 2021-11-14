# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...data.ec_table import ECTable
from ...data.id_table import IDTable
from ...network.network import Network


class ReactionRemoverHelper:

    @classmethod
    def remove_list_of_reactions(
            cls, network: Network, reaction_table: (ECTable, IDTable),
            reverse_remove: bool = False, inplace=False) -> Network:

        if inplace:
            new_net = network
        else:
            new_net: Network = network.copy()
        
        rxn_dict: dict = new_net.reactions.copy()
        if isinstance(reaction_table, ECTable):
            ec_list: list = reaction_table.get_ec_numbers()
            for k, rxn in rxn_dict:
                ec_number = rxn.enzyme.get("ec_number")
                is_in_list = (ec_number in ec_list)
                if reverse_remove:
                    if not is_in_list:
                        new_net.remove_reaction(rxn.id)
                elif is_in_list:
                    new_net.remove_reaction(rxn.id)
        elif isinstance(reaction_table, IDTable):
            id_list: list = reaction_table.get_ids()
            for k, rxn in rxn_dict:
                is_in_list = (rxn.rhea_id in id_list) or (k in id_list)
                if reverse_remove:
                    if not is_in_list:
                        new_net.remove_reaction(rxn.id)
                elif is_in_list:
                    new_net.remove_reaction(rxn.id)
        return new_net
