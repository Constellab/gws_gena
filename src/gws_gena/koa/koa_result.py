# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import (BadRequestException, BarPlotView, ConfigParams,
                      DataFrameRField, ListParam, ListRField, MultiViews,
                      Resource, ResourceRField, ResourceSet, StrParam, Table,
                      resource_decorator, view)
from pandas import DataFrame

from ..twin.twin import Twin


@resource_decorator("KOAResult", human_name="KOA result",
                    short_description="Knockout analysis result", hide=True)
class KOAResult(ResourceSet):
    """
    KOAResultTable

    Result of the Knock-out analysis
    """

    FLUX_TABLE_NAME = "Flux table"
    _twin: Twin = ResourceRField()

    def __init__(self, data: DataFrame = None, twin: Twin = None):
        super().__init__()
        if twin is not None:
            if not isinstance(twin, Twin):
                raise BadRequestException("A twin is required")

            flux_table = Table(data=data)
            flux_table.name = self.FLUX_TABLE_NAME
            self.add_resource(flux_table)

            self._twin = twin
            self._set_technical_info()

    def get_twin(self):
        """ Get the realted twin """
        return self._twin

    def get_flux_table(self):
        """ Get the flux table """
        return self.get_resource(self.FLUX_TABLE_NAME)

    def get_flux_dataframe(self):
        """ Get the flux table """
        return self.get_resource(self.FLUX_TABLE_NAME).get_data()

    def get_ko_ids(self) -> List[str]:
        """ Get the ids of the knock-outed reactions """
        return self.get_flux_dataframe().loc[:, "ko_id"].unique().tolist()

    def _set_technical_info(self):
        pass

    # @view(view_type=MultiViews, human_name='KO Summary', short_description='View KO summary as 2D-bar plots',
    #       specs={
    #           "flux_names":
    #           ListParam(
    #               human_name="Flux names",
    #               short_description="Fluxes to plot. Set 'biomass' to only the plot biomass reaction flux.")})
    # def view_ko_summary_as_bar_plot(self, params: ConfigParams) -> MultiViews:
    #     """
    #     View one or several columns as 2D-bar plots
    #     """

    #     flux_names = params.get_value("flux_names", [])
    #     nb_of_ko = len(self.get_ko_ids())
    #     nb_cols = 3 if nb_of_ko >= 5 else min(2, nb_of_ko)
    #     multi_view = MultiViews(nb_of_columns=nb_cols)
    #     for flux_name in flux_names:
    #         idx = self.get_flux_dataframe()["flux_name"] == flux_name
    #         current_data = self.get_flux_dataframe().loc[idx, :]
    #         x_label = "ko_id"
    #         y_label = flux_name
    #         barplot_view = BarPlotView()
    #         barplot_view.add_series(
    #             y=current_data.values.tolist()
    #         )
    #         multi_view.add_view(
    #             barplot_view,
    #             params={
    #                 "column_names": ["flux_value"],
    #                 "x_label": x_label,
    #                 "y_label": y_label,
    #                 "x_tick_labels": list(current_data.loc[:, "ko_id"].to_list())
    #             })

    #     return multi_view

    @view(view_type=BarPlotView, human_name='KO Summary', short_description='View KO summary as 2D-bar plots',
          specs={
              "flux_name":
              StrParam(
                  human_name="Flux name",
                  optional=True,
                  short_description="Flux to plot. Set 'biomass' to only the plot biomass reaction flux.")})
    def view_ko_summary_as_bar_plot(self, params: ConfigParams) -> BarPlotView:
        """
        View one or several columns as 2D-bar plots
        """

        flux_name = params.get_value("flux_name")
        if flux_name:
            idx = self.get_flux_dataframe()["flux_name"] == flux_name
            current_data = self.get_flux_dataframe().loc[idx, "flux_value"]
        else:
            current_data = self.get_flux_dataframe().loc[:, "flux_value"]

        barplot_view = BarPlotView()
        barplot_view.add_series(
            y=current_data.values.tolist()
        )
        barplot_view.x_tick_labels = self.get_ko_ids()
        return barplot_view
