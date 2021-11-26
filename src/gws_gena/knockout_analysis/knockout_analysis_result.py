# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import (BadRequestException, BarPlotView, ConfigParams,
                      DataFrameRField, ListParam, ListRField, MultiViews,
                      Resource, ResourceRField, Table, resource_decorator,
                      view)
from pandas import DataFrame


@resource_decorator("KnockOutAnalysisResult")
class KnockOutAnalysisResult(Resource):
    _data: DataFrame = DataFrameRField()
    _ko_table: Table = ResourceRField()

    def __init__(self, data, monitored_fluxes, ko_table, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data = data
        self._ko_table = ko_table

    def __str__(self):
        return self._data.__str__()

    def get_flux_table_by_ko(selk, ko_name):
        pass

    @view(view_type=MultiViews,
          human_name='BarPlots',
          short_description='View KO results as 2D-bar plots',
          specs={"flux_names": ListParam(human_name="Flux names", short_description="Fluxes to plot")})
    def view_as_bar_plot(self, params: ConfigParams) -> MultiViews:
        """
        View one or several columns as 2D-bar plots
        """

        flux_names = params.get_value("flux_names", [])
        nb_of_ko = self._ko_table.nb_rows
        nb_cols = max(2, min(2, nb_of_ko))
        multi_view = MultiViews(nb_of_columns=nb_cols)
        for flux_name in flux_names:
            current_data = self._data.loc[flux_name, :]
            x_label = "KO"
            y_label = flux_name
            barplot_view = BarPlotView(current_data)
            multi_view.add_view(
                barplot_view,
                params={
                    "column_names": ["value"],
                    "x_label": x_label,
                    "y_label": y_label,
                    "x_tick_labels": list(current_data.loc[:, "KO"].to_list())
                })

        return multi_view
