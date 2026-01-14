import pandas as pd
from pandas import DataFrame, Series

from ....helper.base_helper import BaseHelper
from ....network.network import Network


class GapFinderHelper(BaseHelper):
    """GapFinderHelper"""

    def find_gaps(self, network: Network) -> DataFrame:
        """Find all gaps"""
        mat: DataFrame = network.create_stoichiometric_matrix()
        mat[mat != 0] = 1
        sum_ = mat.sum(axis=1)
        orphan_mat: Series = sum_ == 0
        deadend_mat: Series = sum_ <= 1

        deadend_df = pd.DataFrame(
            {
                "is_dead_end": deadend_mat,
                "is_orphan": orphan_mat,
            }
        )

        data = network.get_steady_compounds()
        names = list(data.keys())
        names = [k for k in names if k in deadend_df.index]
        deadend_df = deadend_df.loc[names, :]

        return deadend_df

    # def has_deadend_compounds(self, network: Network) -> bool:
    #     """ Returns True if the network has deadend metabolites; False otherwise """
    #     return len(self.find_deadend_compound_ids(network))

    def find_orphan_compound_ids(self, network: Network) -> list[str]:
        """Find only orphan compounds as list"""
        df = self.find_gaps(network)
        comp_ids = [idx for idx in df.index if df.at[idx, "is_orphan"]]
        return comp_ids

    def find_deadend_compound_ids(self, network: Network) -> list[str]:
        """Find dead-end compounds as list"""
        df = self.find_gaps(network)
        comp_ids = [idx for idx in df.index if df.at[idx, "is_dead_end"]]
        return comp_ids
