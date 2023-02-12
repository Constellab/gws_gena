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
            ec_number_tab = []
            for enzyme in rxn.enzymes:
                ec_number_tab.append(enzyme.get("ec_number"))
            all_valid_ids.extend([*ec_number_tab, rxn.id, rxn.rhea_id])

        if isinstance(reaction_table, (EntityIDTable, ECTable)):
            if isinstance(reaction_table, EntityIDTable):
                id_list: list = reaction_table.get_ids()
            else:
                id_list: list = reaction_table.get_ec_numbers()

            valid_ids_to_remove = [x for x in id_list if x in all_valid_ids]
            invalid_ids_to_remove = [x for x in id_list if x not in all_valid_ids]

            if valid_ids_to_remove:
                for k, rxn in rxn_series.items():
                    ec_number_tab = []
                    for enzyme in rxn.enzymes:
                        ec_number_tab.append(enzyme.get("ec_number"))

                    rxn_ids = [*ec_number_tab, rxn.id, rxn.rhea_id]
                    is_in_list = False
                    for rxn_id in rxn_ids:
                        is_in_list = rxn_id in valid_ids_to_remove
                        if is_in_list:
                            break

                    if reverse_remove:
                        if not is_in_list:
                            network.remove_reaction(rxn.id)
                    elif is_in_list:
                        network.remove_reaction(rxn.id)

            if invalid_ids_to_remove:
                self.log_warning_message(
                    f"The following reactions were not found. Please check ids.\n{invalid_ids_to_remove}")

        else:
            self.log_warning_message("Invalid reaction table")
