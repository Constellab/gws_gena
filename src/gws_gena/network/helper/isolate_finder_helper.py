# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import Table
from pandas import DataFrame

from ...network.network import Network


class IsolateFinderHelper:

    @staticmethod
    def find(network: Network) -> Table:
        """ Find isolates """
        # S: DataFrame = network.create_steady_stoichiometric_matrix()
        # sum_S = S.sum(axis=1)
