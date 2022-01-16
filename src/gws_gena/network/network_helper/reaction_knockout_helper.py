# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...data.ec_table import ECTable
from ...data.entity_id_table import EntityIDTable
from ...network.network import Network


class ReactionKnockOutHelper:

    FLUX_EPSILON = 1e-9

    @classmethod
    def knockout_list_of_reactions(
            cls, network: Network, reaction_table: (ECTable, EntityIDTable),
            ko_delimiter=None, current_task=None, inplace=False) -> Network:
        if inplace:
            new_net = network
        else:
            new_net: Network = network.copy()

        all_ids = []
        found_id = []

        if isinstance(reaction_table, ECTable):
            # ko using EC_NUMBER only
            ec_list: list = reaction_table.get_ec_numbers()
            for _, rxn in new_net.reactions.items():
                ec_number_str = rxn.enzyme.get("ec_number")
                if ko_delimiter:
                    ec_numbers = ec_number_str.split(ko_delimiter)
                else:
                    ec_numbers = [ec_number_str]
                all_ids.extend(ec_numbers)

                for ec_number in ec_numbers:
                    for ko_ec in ec_list:
                        if ec_number == ko_ec:
                            rxn.lower_bound = -cls.FLUX_EPSILON
                            rxn.upper_bound = cls.FLUX_EPSILON
                            found_id.append(ec_number)

        elif isinstance(reaction_table, EntityIDTable):
            # ko using RXN_ID and EC_NUMBER
            id_list: list = reaction_table.get_ids()
            for rxn_id, rxn in new_net.reactions.items():
                rhea_id = rxn.rhea_id
                ec_number = rxn.enzyme.get("ec_number")
                for _, ko_id_str in enumerate(id_list):
                    if ko_delimiter:
                        ko_ids = ko_id_str.split(ko_delimiter)
                    else:
                        ko_ids = [ko_id_str]
                    all_ids.extend(ko_ids)

                    for ko_id in ko_ids:
                        if ko_id in [rxn_id, rhea_id, ec_number]:
                            rxn.lower_bound = -cls.FLUX_EPSILON
                            rxn.upper_bound = cls.FLUX_EPSILON
                            found_id.append(ko_id)

        # write warnings
        not_found_id = []
        all_ids = list(set(all_ids))
        for ko_id in all_ids:
            if ko_id not in found_id:
                not_found_id.append(ko_id)
                if current_task:
                    current_task.log_warning_message(
                        f"The KO ID '{ko_id}' is not found. Please check the KO table.")

        return new_net, not_found_id
