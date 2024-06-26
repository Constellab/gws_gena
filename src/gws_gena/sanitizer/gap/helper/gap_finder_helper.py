
from typing import List

import pandas as pd
from pandas import DataFrame, Series

from ....helper.base_helper import BaseHelper
from ....network.network import Network


class GapFinderHelper(BaseHelper):
    """ GapFinderHelper """

    def find_gaps(self, network: Network) -> DataFrame:
        """ Find all gaps """
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

    # def has_deadend_compounds(self, network: Network) -> bool:
    #     """ Returns True if the network has deadend metabolites; False otherwise """
    #     return len(self.find_deadend_compound_ids(network))

    def find_orphan_compound_ids(self, network: Network) -> List[str]:
        """ Find only orphan compounds as list """
        df = self.find_gaps(network)
        comp_ids = [idx for idx in df.index if df.at[idx, "is_orphan"]]
        return comp_ids

    def find_deadend_compound_ids(self, network: Network) -> List[str]:
        """ Find dead-end compounds as list """
        df = self.find_gaps(network)
        comp_ids = [idx for idx in df.index if df.at[idx, "is_dead_end"]]
        return comp_ids
