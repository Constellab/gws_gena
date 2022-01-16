# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import Logger

from ...data.ec_table import ECTable
from ...data.entity_id_table import EntityIDTable
from ...network.network import Network


class ReactionRemoverHelper:

    @classmethod
    def remove_list_of_reactions(
            cls, network: Network, reaction_table: (ECTable, EntityIDTable),
            reverse_remove: bool = False, inplace=False, current_task=None) -> Network:

        if inplace:
            new_net = network
        else:
            new_net: Network = network.copy()

        rxn_dict: dict = new_net.reactions.copy()

        # check all
        all_valid_ids = []
        for k, rxn in rxn_dict.items():
            ec_number = rxn.enzyme.get("ec_number")
            all_valid_ids.extend([ec_number, rxn.id, rxn.rhea_id])

        if isinstance(reaction_table, ECTable):
            ec_list: list = reaction_table.get_ec_numbers()
            valid_id_list = [x for x in ec_list if x in all_valid_ids]
            invalid_id_list = [x for x in ec_list if x not in all_valid_ids]

            if valid_id_list:
                for k, rxn in rxn_dict.items():
                    ec_number = rxn.enzyme.get("ec_number")
                    is_in_list = (ec_number in valid_id_list)
                    if reverse_remove:
                        if not is_in_list:
                            new_net.remove_reaction(rxn.id)
                    elif is_in_list:
                        new_net.remove_reaction(rxn.id)

        elif isinstance(reaction_table, EntityIDTable):
            id_list: list = reaction_table.get_ids()
            valid_id_list = [x for x in id_list if x in all_valid_ids]
            invalid_id_list = [x for x in id_list if x not in all_valid_ids]

            if valid_id_list:
                for k, rxn in rxn_dict.items():
                    is_in_list = (rxn.rhea_id in valid_id_list) or (k in valid_id_list)
                    if reverse_remove:
                        if not is_in_list:
                            new_net.remove_reaction(rxn.id)
                    elif is_in_list:
                        new_net.remove_reaction(rxn.id)

        for k in invalid_id_list:
            if isinstance(reaction_table, ECTable):
                message = f"The EC '{k}' is not found. Please check the EC table."
            else:
                message = f"The ID '{k}' is not found. Please check the ID table."

            if current_task:
                current_task.log_warning_message(message)
            else:
                Logger.warning(message)

        return new_net
