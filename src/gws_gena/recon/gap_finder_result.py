# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BoolParam, DictRField, Resource, Table, TabularView,
                      resource_decorator, view)
from pandas import DataFrame


@resource_decorator("GapFinderResult", human_name="Gap finder result", hide=True)
class GapFinderResult(Resource):
    """
    GapFinderResult class
    """

    gaps_data = DictRField()

    def __init__(self, gaps=None):
        super().__init__()
        if gaps:
            self.gaps_data = gaps

    def get_gaps_as_json(self):
        """ Get gaps as json """
        return self.gaps_data

    def count_number_of_dead_ends(self) -> int:
        return self.get_compounds_as_dataframe(dead_ends_only=True).shape[0]

    def count_number_of_orphans(self) -> int:
        return self.get_compounds_as_dataframe(orphans_only=True).shape[0]

    @view(view_type=TabularView, human_name="Compound table", specs={
        "dead_ends_only": BoolParam(default_value=False)
    })
    def view_compounds_as_table(self, dead_ends_only=False, **kwargs) -> TabularView:
        """ View compounds as table """
        data = self.get_compounds_as_dataframe(dead_ends_only=dead_ends_only, **kwargs)
        t_view = TabularView()
        t_view.set_data(data=data)
        return t_view

    def get_compounds_as_dataframe(self, dead_ends_only=False, orphans_only=False, **kwargs) -> DataFrame:
        """ View compounds as dataframe """
        df: DataFrame = DataFrame.from_dict(
            self.gaps_data["compounds"],
            columns=["is_substrate", "is_product", "is_dead_end", "is_orphan"],
            orient="index"
        )

        if orphans_only:
            df = df[df.is_orphan == True]
        elif dead_ends_only:
            df = df[df.is_dead_end == True]
        return df

    @view(view_type=TabularView, human_name="Reaction table",
          specs={
              "dead_ends_only":
              BoolParam(default_value=False, short_description="True to only see reactions having gaps")})
    def view_reactions_as_table(self, dead_ends_only=False, **kwargs) -> TabularView:
        data = self.get_reactions_as_dataframe(dead_ends_only=dead_ends_only, **kwargs)
        t_view = TabularView()
        t_view.set_data(data=data)
        return t_view

    def get_reactions_as_dataframe(self, dead_ends_only=False, **kwargs) -> Table:
        df: DataFrame = DataFrame.from_dict(
            self.gaps_data["reactions"],
            columns=["name", "has_gap"],
            orient="index"
        )
        if dead_ends_only:
            df = df[df.has_gap == True]
        return df

    @view(view_type=TabularView, human_name="Pathway table", specs={
        "dead_ends_only": BoolParam(default_value=False, short_description="True to only see pathways having gaps")
    })
    def view_pathways_as_table(self, dead_ends_only=False, **kwargs) -> TabularView:
        data = self.get_pathways_as_dataframe(dead_ends_only=dead_ends_only, **kwargs)
        t_view = TabularView()
        t_view.set_data(data=data)
        return t_view

    def get_pathways_as_dataframe(self, dead_ends_only=False, **kwargs) -> Table:
        df: DataFrame = DataFrame.from_dict(
            self.gaps_data["pathways"],
            columns=["name", "nb_reactions", "nb_gaps", "gap_ratio"],
            orient="index"
        )
        if dead_ends_only:
            df = df[:, df["nb_gaps"] > 0]
        return df
