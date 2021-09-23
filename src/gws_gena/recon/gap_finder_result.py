# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from gws_core import Resource, resource_decorator
from gws_core import DictView, DictRField

@resource_decorator("GapFinderResult")
class GapFinderResult(Resource):
    """
    GapFinderResult class
    """

    gaps_data = DictRField()

    def __init__(self, *args, gaps=None, **kwargs):
        super().__init__(*args, **kwargs)
        if gaps:
            self.gaps_data = gaps
 
    def render__gaps__as_json(self):
        return self.gaps_data

    def render__compounds__as_table(self, filter_gaps_only=False, **kwargs) -> DataFrame:
        table: DataFrame = DictView.to_table(
            self.gaps_data["compounds"], 
            columns=["is_substrate", "is_product", "is_gap"]
        )
        if filter_gaps_only:
            table = table[ :, table["is_gap"] == True ]
        return table


    def render__reactions__as_table(self, filter_gaps_only=False, **kwargs) -> DataFrame:
        table: DataFrame = DictView.to_table(
            self.gaps_data["reactions"], 
            columns=["name", "has_gap"]
        )
        if filter_gaps_only:
            table = table[ :, table["has_gap"] == True ]
        return table

    def render__pathways__as_table(self, filter_gaps_only=False, **kwargs) -> DataFrame:
        table: DataFrame = DictView.to_table(
            self.gaps_data["pathways"], 
            columns=["name", "nb_reactions", "nb_gaps", "gap_ratio"]
        )
        if filter_gaps_only:
            table = table[ :, table["nb_gaps"] > 0 ]
        return table
