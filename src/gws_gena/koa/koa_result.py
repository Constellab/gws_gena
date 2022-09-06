# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union

from gws_core import (BadRequestException, BarPlotView, ConfigParams,
                      DataFrameRField, ListParam, ListRField, MultiViews,
                      Resource, ResourceRField, ResourceSet, StringHelper,
                      StrParam, Table, TechnicalInfo, resource_decorator, view)
from pandas import DataFrame

from ..data.ec_table import ECTable
from ..data.entity_id_table import EntityIDTable
from ..twin.twin import Twin


@resource_decorator("KOAResult", human_name="KOA result",
                    short_description="Knockout analysis result", hide=True)
class KOAResult(ResourceSet):
    """
    KOAResultTable

    Result of the Knock-out analysis
    """

    FLUX_TABLE_NAME = "Flux table"
    _simulations = ListRField()
    _twin: Twin = ResourceRField()
    _ko_table: Twin = ResourceRField()

    def __init__(self, data: List[DataFrame] = None, twin: Twin = None, ko_table: Union[ECTable, EntityIDTable] = None):
        super().__init__()
        if twin is None:
            self._simulations = []
        else:
            if not isinstance(twin, Twin):
                raise BadRequestException("A twin is required")

            if not isinstance(ko_table, (ECTable, EntityIDTable)):
                raise BadRequestException("The ko table must be an isntance of ECTable or EntityIDTable")

            self._twin = twin
            self._ko_table = ko_table

            ko_ids = ko_table.get_ids()
            for i, current_data in enumerate(data):
                flux_df = current_data["fluxes"]
                invalid_ko_ids = current_data["invalid_ko_ids"]
                flux_table = Table(data=flux_df)
                flux_table.name = self._create_flux_table_name(ko_ids[i])
                flux_table.add_technical_info(TechnicalInfo(key="invalid_ko_ids", value=f"{invalid_ko_ids}"))
                self.add_resource(flux_table)

            self._set_technical_info()

    # -- C --

    def _create_flux_table_name(self, ko_id):
        slug_id = StringHelper.slugify(ko_id, snakefy=True, to_lower=False)
        return f"{self.FLUX_TABLE_NAME} - {slug_id}"

    # -- G --

    def get_simulations(self):
        """ Get simulations """
        return self._simulations

    def get_twin(self):
        """ Get the realted twin """
        return self._twin

    def get_flux_table(self, ko_id):
        """ Get the flux table """
        name = self._create_flux_table_name(ko_id)
        return self.get_resource(name)

    def get_flux_dataframe(self, ko_id):
        """ Get the flux table """
        name = self._create_flux_table_name(ko_id)

        return self.get_resource(name).get_data()

    def get_ko_ids(self) -> List[str]:
        """ Get the ids of the knock-outed reactions """
        return self._ko_table.get_ids()

    # -- S --

    def set_simulations(self, simulations: list):
        """ Set simulations """
        if not isinstance(simulations, list):
            raise BadRequestException("The simulations must be a list")
        self._simulations = simulations

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
