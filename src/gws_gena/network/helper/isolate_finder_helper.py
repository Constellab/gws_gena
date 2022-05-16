# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import Table
from pandas import DataFrame

from ...network.network import Network


class IsolateFinder:

    @staticmethod
    def find(network: Network) -> Table:

        S: DataFrame = network.create_steady_stoichiometric_matrix()
        sum_S = S.sum(axis=1)
        print(sum_S)

        pass
