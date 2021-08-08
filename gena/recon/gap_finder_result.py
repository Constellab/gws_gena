# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from gws.resource import Resource
from gws.view import DictView

class GapFinderResult(Resource):
    """
    GapFinderResult class
    """

    def __init__(self, *args, gaps=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            if gaps:
                self.data['gaps'] = gaps 
            else:
                self.data['gaps'] = {}

    def render__gaps__as_json(self):
        return self.data["gaps"]

    def render__compounds__as_table(self, filter_gaps_only=False, stringify=False, **kwargs) -> (str, DataFrame,):
        table: DataFrame = DictView.to_table(
            self.data["gaps"]["compounds"], 
            columns=["is_substrate", "is_product", "is_gap"]
        )

        if filter_gaps_only:
            table = table[ :, table["is_gap"] == True ]

        if stringify:
            return table.to_csv()
        else:
            return table

    def render__reactions__as_table(self, filter_gaps_only=False, stringify=False, **kwargs) -> (str, DataFrame,):
        table: DataFrame = DictView.to_table(
            self.data["gaps"]["reactions"], 
            columns=["name", "has_gap"]
        )

        if filter_gaps_only:
            table = table[ :, table["has_gap"] == True ]

        if stringify:
            return table.to_csv()
        else:
            return table

    def render__pathways__as_table(self, filter_gaps_only=False, stringify=False, **kwargs) -> (str, DataFrame,):
        table: DataFrame = DictView.to_table(
            self.data["gaps"]["pathways"], 
            columns=["name", "nb_reactions", "nb_gaps", "gap_ratio"]
        )

        if filter_gaps_only:
            table = table[ :, table["nb_gaps"] > 0 ]

        if stringify:
            return table.to_csv()
        else:
            return table