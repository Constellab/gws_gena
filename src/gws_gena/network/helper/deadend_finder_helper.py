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
        #mat: DataFrame = network.create_steady_stoichiometric_matrix()
        mat: DataFrame = network.create_stoichiometric_matrix()
        mat[mat != 0] = 1
        sum_ = mat.sum(axis=1)
        orphan_mat: Series = (sum_ == 0)
        deadend_mat: Series = (sum_ <= 1)

        deadend_mat = pd.concat([
            deadend_mat.to_frame(name="is_dead_end"),
            orphan_mat.to_frame(name="is_orphan"),
        ], axis=1)

        data = network.get_steady_compounds()
        names = list(data.keys())
        names = [k for k in names if k in deadend_mat.index]
        deadend_mat = deadend_mat.loc[names, :]

        return deadend_mat
