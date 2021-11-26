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
            cls, network: Network, reaction_table: (ECTable, IDTable),
            reverse_knockout: bool = False, inplace=False) -> Network:
        if inplace:
            new_net = network
        else:
            new_net: Network = network.copy()

        if isinstance(reaction_table, ECTable):
            ec_list: list = reaction_table.get_ec_numbers()
            for _, rxn in new_net.reactions.items():
                ec_number = rxn.enzyme.get("ec_number")
                is_in_list = (ec_number in ec_list)
                if reverse_knockout:
                    if not is_in_list:
                        rxn.lower_bound = -cls.FLUX_EPSILON
                        rxn.upper_bound = cls.FLUX_EPSILON
                elif is_in_list:
                    rxn.lower_bound = -cls.FLUX_EPSILON
                    rxn.upper_bound = cls.FLUX_EPSILON
        elif isinstance(reaction_table, IDTable):
            id_list: list = reaction_table.get_ids()
            for k, rxn in new_net.reactions.items():
                is_in_list = (rxn.rhea_id in id_list) or (k in id_list)
                if reverse_knockout:
                    if not is_in_list:
                        rxn.lower_bound = -cls.FLUX_EPSILON
                        rxn.upper_bound = cls.FLUX_EPSILON
                elif is_in_list:
                    rxn.lower_bound = -cls.FLUX_EPSILON
                    rxn.upper_bound = cls.FLUX_EPSILON
        return new_net
