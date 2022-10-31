# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ....data.ec_table import ECTable
from ....data.entity_id_table import EntityIDTable
from ....helper.base_helper import BaseHelper
from ...network import Network


class ReactionRemoverHelper(BaseHelper):

    def remove_list_of_reactions(
            self, network: Network, reaction_table: (ECTable, EntityIDTable),
            reverse_remove: bool = False) -> Network:
        """ Remove a list of reactions for a network """
        rxn_series = network.reactions.copy()

        # check all
        all_valid_ids = []
        for k, rxn in rxn_series.items():
            ec_number = rxn.enzyme.get("ec_number")
            all_valid_ids.extend([ec_number, rxn.id, rxn.rhea_id])

        if isinstance(reaction_table, ECTable):
            ec_list: list = reaction_table.get_ec_numbers()
            valid_id_list = [x for x in ec_list if x in all_valid_ids]
            invalid_id_list = [x for x in ec_list if x not in all_valid_ids]

            if valid_id_list:
                for k, rxn in rxn_series.items():
                    ec_number = rxn.enzyme.get("ec_number")
                    is_in_list = (ec_number in valid_id_list)
                    if reverse_remove:
                        if not is_in_list:
                            network.remove_reaction(rxn.id)
                    elif is_in_list:
                        network.remove_reaction(rxn.id)

        elif isinstance(reaction_table, EntityIDTable):
            id_list: list = reaction_table.get_ids()
            valid_id_list = [x for x in id_list if x in all_valid_ids]
            invalid_id_list = [x for x in id_list if x not in all_valid_ids]

            if valid_id_list:
                for k, rxn in rxn_series.items():
                    is_in_list = (rxn.rhea_id in valid_id_list) or (k in valid_id_list)
                    if reverse_remove:
                        if not is_in_list:
                            network.remove_reaction(rxn.id)
                    elif is_in_list:
                        network.remove_reaction(rxn.id)

        for k in invalid_id_list:
            if isinstance(reaction_table, ECTable):
                message = f"The EC '{k}' is not found. Please check the EC table."
            else:
                message = f"The ID '{k}' is not found. Please check the ID table."
            self.log_warning_message(message)