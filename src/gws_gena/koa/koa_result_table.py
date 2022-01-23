# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import (BadRequestException, BarPlotView, ConfigParams,
                      DataFrameRField, ListParam, ListRField, MultiViews,
                      Resource, ResourceRField, Table, resource_decorator,
                      view)


@resource_decorator("KOAResultTable", human_name="KOA result table", short_description="Knockout analysis result table", hide=True)
class KOAResultTable(Table):

    def get_ko_ids(self) -> List[str]:
        return self._data.loc[:, "ko_id"].unique()

    @view(view_type=MultiViews,
          human_name='KO Summary',
          short_description='View KO summary as 2D-bar plots',
          specs={"flux_names": ListParam(human_name="Flux names", short_description="Fluxes to plot")})
    def view_ko_summary_as_bar_plot(self, params: ConfigParams) -> MultiViews:
        """
        View one or several columns as 2D-bar plots
        """

        flux_names = params.get_value("flux_names", [])
        nb_of_ko = len(self.get_ko_ids())
        nb_cols = 3 if nb_of_ko >= 5 else min(2, nb_of_ko)
        multi_view = MultiViews(nb_of_columns=nb_cols)
        for flux_name in flux_names:
            idx = self._data["flux_name"] == flux_name
            current_data = self._data.loc[idx, :]
            x_label = "ko_id"
            y_label = flux_name
            barplot_view = BarPlotView()
            barplot_view.add_series(
                y=current_data.values.tolist()
            )
            multi_view.add_view(
                barplot_view,
                params={
                    "column_names": ["flux_value"],
                    "x_label": x_label,
                    "y_label": y_label,
                    "x_tick_labels": list(current_data.loc[:, "ko_id"].to_list())
                })

        return multi_view
