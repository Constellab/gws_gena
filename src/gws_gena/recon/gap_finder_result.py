# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from gws_core import Resource, resource_decorator
from gws_core import DictView

@resource_decorator("GapFinderResult")
class GapFinderResult(Resource):
    """
    GapFinderResult class
    """

    def __init__(self, *args, gaps=None, **kwargs):
        super().__init__(*args, **kwargs)
        if 'gaps' not in self.binary_store:
            gaps = gaps if gaps else {}
            self._set_gaps_dict_in_store(gaps)

    def get_gaps_data(self) -> dict:
        return self._get_gaps_dict_from_store()

    def _get_gaps_dict_from_store(self) -> dict:
        return self.binary_store.get('gaps',{})

    def render__gaps__as_json(self):
        return self._get_gaps_dict_from_store()

    def render__compounds__as_table(self, filter_gaps_only=False, stringify=False, **kwargs) -> (str, DataFrame,):
        table: DataFrame = DictView.to_table(
            self.get_gaps_data()["compounds"], 
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
            self.get_gaps_data()["reactions"], 
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
            self.get_gaps_data()["pathways"], 
            columns=["name", "nb_reactions", "nb_gaps", "gap_ratio"]
        )

        if filter_gaps_only:
            table = table[ :, table["nb_gaps"] > 0 ]

        if stringify:
            return table.to_csv()
        else:
            return table

    def _set_gaps_dict_in_store(self, gaps):
        self.binary_store['gaps'] = gaps