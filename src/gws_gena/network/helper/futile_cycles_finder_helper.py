# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import Table
from pandas import DataFrame

from ...network.network import Network


class FutileCyclesFinderHelper:

    @staticmethod
    def find(network: Network) -> Table:
        """ Find futile cycle """

        # S = network.create_stoichiometric_matrix()
        # for i in range(0, S.shape[1]):
        #     Ri = S[:, i]
        #     for j in range(i, S.shape[1]):
        #         Rj = S[:, j]
        #         if all(Ri == Rj):
        #             pass
