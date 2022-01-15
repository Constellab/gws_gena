# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union

import pandas as pd
from gws_core import (BadRequestException, ConfigParams, HeatmapView,
                      HistogramView, Resource, ResourceRField, RField,
                      StrParam, Table, TableView, resource_decorator, view)
from pandas import DataFrame
from scipy import stats

from ..network.network import Network
from ..network.reaction import Reaction, ReactionPathways
from ..twin.flat_twin import FlatTwin
from ..twin.twin import Twin


class OptimizeResult:
    """
    OptimizeResult class.

    A simple proxy of SciPy OptimizeResult
    """

    def __init__(self, res: dict):
        self.x = res["x"]
        self.xmin = res["xmin"]
        self.xmax = res["xmax"]
        self.x_names = res["x_names"]
        self.constraints = res["constraints"]
        self.constraint_names = res["constraint_names"]
        self.niter = res["niter"]
        self.message = res["message"]
        self.success = res["success"]
        self.status = res["status"]


@resource_decorator("FBAResult", human_name="FBAResult", short_description="Flux Balance Analysis Result")
class FBAResult(Resource):
    """
    FBAResult class
    """

    twin: Twin = ResourceRField()
    optimize_result = RField(default_value=None)

    _annotated_twin = None
    _default_zero_flux_threshold = 0.01
    _flux_table: Table = None

    def __init__(self, twin: Twin = None, optimize_result: OptimizeResult = None):
        super().__init__()
        if twin is not None:
            if not isinstance(twin, Twin):
                raise BadRequestException("A twin is required")

            self.twin = twin
            self.optimize_result = optimize_result

    # -- C --

    def compute_zero_flux_threshold(self) -> (float, float):
        df = self.get_sv_as_table().get_data()
        val = df["value"]
        try:
            if val.shape[0] >= 20:
                _, p = stats.normaltest(val)
                if p < 0.05:
                    return 2.0 * val.std(), p
                else:
                    return self._default_zero_flux_threshold, None
            else:
                return self._default_zero_flux_threshold, None
        except:
            return self._default_zero_flux_threshold, None

    # -- G --

    def get_related_twin(self):
        return self.twin

    def get_fluxes_by_reaction_ids(self, reaction_ids: Union[List, str]) -> DataFrame:
        if isinstance(reaction_ids, str):
            reaction_ids = [reaction_ids]
        if not isinstance(reaction_ids, list):
            raise BadRequestException("A str or a list of str is required")
        df = self.get_fluxes_as_table().get_data()
        #idx = df.index[df['reaction_id'].isin(reaction_ids)]
        return df.loc[reaction_ids, :]

    def get_sv_by_compound_ids(self, compound_ids: Union[List, str]) -> DataFrame:
        if isinstance(compound_ids, str):
            compound_ids = [compound_ids]
        if not isinstance(compound_ids, list):
            raise BadRequestException("A str or a list of str is required")
        df = self.get_sv_as_table().get_data()
        #idx = df.index[df['compound_id'].isin(compound_ids)]
        return df.loc[compound_ids, :]

    def get_fluxes_as_table(self) -> Table:
        if self._flux_table:
            return self._flux_table

        res: OptimizeResult = self.optimize_result
        val = DataFrame(data=res.x, index=res.x_names, columns=["value"])

        if res.xmin is None:
            lb = DataFrame(data=res.x, index=res.x_names, columns=["lower_bound"])
        else:
            lb = DataFrame(data=res.xmin, index=res.x_names, columns=["lower_bound"])

        if res.xmax is None:
            ub = DataFrame(data=res.x, index=res.x_names, columns=["upper_bound"])
        else:
            ub = DataFrame(data=res.xmax, index=res.x_names, columns=["upper_bound"])

        kegg_pw = []
        brenda_pw = []
        metacyc_pw = []

        if isinstance(self.twin, FlatTwin):
            flat_twin: FlatTwin = self.twin
        else:
            flat_twin: FlatTwin = self.twin.flatten()

        net: Network = flat_twin.get_flat_network()
        rxn: Reaction
        pathways: ReactionPathways
        for rxn_id in res.x_names:
            if rxn_id in net.reactions:
                rxn = net.reactions[rxn_id]
                pathways = rxn.get_pathways_as_flat_dict()
                kegg_pw.append(pathways.get("kegg", ""))
                brenda_pw.append(pathways.get("brenda", ""))
                metacyc_pw.append(pathways.get("metacyc", ""))
            else:
                kegg_pw.append("")
                brenda_pw.append("")
                metacyc_pw.append("")

        brenda_pw = DataFrame(data=brenda_pw, index=res.x_names, columns=["brenda"])
        kegg_pw = DataFrame(data=kegg_pw, index=res.x_names, columns=["kegg"])
        metacyc_pw = DataFrame(data=metacyc_pw, index=res.x_names, columns=["metacyc"])
        df = pd.concat([val, lb, ub, brenda_pw, kegg_pw, metacyc_pw], axis=1)
        # if drop_index:
        #     df.reset_index(inplace=True)
        #     df.rename(columns={'index': 'reaction_id'}, inplace=True)
        self._flux_table = Table(data=df)
        return self._flux_table

    def get_sv_as_table(self) -> Table:
        res: OptimizeResult = self.optimize_result
        df = DataFrame(data=res.constraints, index=res.constraint_names, columns=["value"])
        # if drop_index:
        #     df.reset_index(inplace=True)
        #     df.rename(columns={'index': 'compound_id'}, inplace=True)
        return Table(data=df)

    def get_annotated_twin_as_json(self) -> dict:
        if not self._annotated_twin:
            from ..twin.helper.twin_annotator_helper import TwinAnnotatorHelper
            twin: Twin = self.get_related_twin()
            self._annotated_twin: Twin = TwinAnnotatorHelper.annotate(twin, self)
        return self._annotated_twin.to_json(deep=True)

    # -- V --

    @view(view_type=TableView, human_name="TableView",
          specs={
              "type":
              StrParam(
                  default_value="fluxes", allowed_values=["fluxes", "SV"],
                  human_name="View type")})
    def view_as_table(self, params: ConfigParams) -> TableView:
        view_type = params.get("type", "fluxes")
        if view_type == "fluxes":
            table: Table = self.get_fluxes_as_table()
        elif view_type == "SV":
            table: Table = self.get_sv_as_table()
        return TableView(table=table)

    @view(view_type=HeatmapView, human_name="HeatmapView",
          specs={
              "type":
              StrParam(
                  default_value="fluxes", allowed_values=["fluxes", "SV"],
                  human_name="View type")})
    def view_as_heatmap(self, params: ConfigParams) -> HeatmapView:
        view_type = params.get("type", "fluxes")
        if view_type == "fluxes":
            table: Table = self.get_fluxes_as_table()
            data = table.get_data()
            data.index = data.index + " [" + table.get_data()["kegg"] + "]"
            data = data.loc[:, ["value", "lower_bound", "upper_bound"]]

            #data.index = table.get_data()["reaction_id"] + " [" + table.get_data()["kegg"] + "]"
            table = Table(data=data)
        elif view_type == "SV":
            table: Table = self.get_sv_as_table()
            data = table.get_data().loc[:, ["value"]]
            #data.index = table.get_data()["compound_id"]
            table = Table(data=data)

        return HeatmapView(table=table)

    @view(view_type=HistogramView, human_name="SV HistogramView", short_description="Steady states distribution")
    def view_sv_as_table(self, params: ConfigParams) -> HistogramView:
        table: Table = self.get_sv_as_table()
        data = table.get_data().loc[:, "value"].tolist()
        hist_view = HistogramView()
        hist_view.add_series(data=data, name="SV Distribution")
        return hist_view
