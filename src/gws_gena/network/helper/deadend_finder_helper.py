# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas as pd
from pandas import DataFrame, Series

from ...network.network import Network


class DeadendFinder:

    @staticmethod
    def find(network: Network) -> DataFrame:
        """ Find dead-end compounds """
        mat: DataFrame = network.create_steady_stoichiometric_matrix()
        sum_ = mat.abs().sum(axis=1)
        orphan_mat: Series = (sum_ == 0)
        deadend_mat: Series = (sum_ <= 1)

        deadend_mat = pd.concat([
            deadend_mat.to_frame(name="is_dead_end"),
            orphan_mat.to_frame(name="is_orphan"),
        ], axis=1)

        return deadend_mat
