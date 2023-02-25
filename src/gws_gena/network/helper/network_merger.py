# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...helper.base_helper import BaseHelper
from ..network import Network


class NetworkMergerHelper(BaseHelper):
    """ NetworkMergerHelper """

    def merge(self, destination_network: Network, source_network: Network, inplace=False):
        """
        Merge two networks
        The input destination_network is augmented after merge
        """

        if not inplace:
            destination_network = destination_network.copy()

        for rxn in source_network.reactions.values():
            if not destination_network.reaction_exists(rxn):
                destination_network.add_reaction(rxn)
            else:
                self.log_info_message(f"Reaction {rxn.id} is ignored. It already exists.")

        return destination_network
