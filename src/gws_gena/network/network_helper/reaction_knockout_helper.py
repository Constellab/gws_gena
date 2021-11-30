# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...data.ec_table import ECTable
from ...data.id_table import IDTable
from ...network.network import Network


class ReactionKnockOutHelper:

    FLUX_EPSILON = 1e-9

    @classmethod
    def knockout_list_of_reactions(
            cls, network: Network, reaction_table: (ECTable, IDTable), current_task=None, inplace=False) -> Network:
        if inplace:
            new_net = network
        else:
            new_net: Network = network.copy()

        if isinstance(reaction_table, ECTable):
            # ko using EC_NUMBER only
            ec_list: list = reaction_table.get_ec_numbers()
            for _, rxn in new_net.reactions.items():
                ec_number = rxn.enzyme.get("ec_number")
                for ko_ec in ec_list:
                    if ec_number == ko_ec:
                        rxn.lower_bound = -cls.FLUX_EPSILON
                        rxn.upper_bound = cls.FLUX_EPSILON
                    else:
                        if current_task:
                            current_task.log_warning_message(
                                f"The EC number '{ko_ec}' is not found. Please check the KO table.")

        elif isinstance(reaction_table, IDTable):
            # ko using RXN_ID and EC_NUMBER
            id_list: list = reaction_table.get_ids()
            for rxn_id, rxn in new_net.reactions.items():
                rhea_id = rxn.rhea_id
                ec_number = rxn.enzyme.get("ec_number")
                for i, ko_id in enumerate(id_list):
                    if ko_id in [rxn_id, rhea_id, ec_number]:
                        rxn.lower_bound = -cls.FLUX_EPSILON
                        rxn.upper_bound = cls.FLUX_EPSILON
                        del id_list[i]

            # ko using CHEBI_ID
            for ko_id in id_list:
                if ko_id.startswith("CHEBI:"):
                    rxns = new_net.get_reactions_related_to_chebi_id(ko_id)
                    if rxns:
                        for rxn in rxns:
                            rxn.lower_bound = -cls.FLUX_EPSILON
                            rxn.upper_bound = cls.FLUX_EPSILON
                    else:
                        if current_task:
                            current_task.log_warning_message(
                                f"The ID number '{ko_id}' is not found. Please check the KO table.")
                else:
                    if current_task:
                        current_task.log_warning_message(
                            f"The ID number '{ko_id}' is not found. Please check the KO table.")

        return new_net
