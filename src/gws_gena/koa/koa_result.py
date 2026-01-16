

from gws_core import (
    BadRequestException,
    BarPlotView,
    ConfigParams,
    ConfigSpecs,
    ListParam,
    ListRField,
    ResourceSet,
    StringHelper,
    Table,
    TechnicalInfo,
    TypingStyle,
    resource_decorator,
    view,
)
from pandas import DataFrame


@resource_decorator("KOAResult", human_name="KOA result",
                    short_description="Knockout analysis result", hide=True,
                    style=TypingStyle.material_icon(material_icon_name='troubleshoot', background_color='#CB4335'))
class KOAResult(ResourceSet):
    """
    KOAResultTable

    Result of the Knock-out analysis
    """

    FLUX_TABLE_NAME = "Flux table"
    _simulations = ListRField()
    # _ko_table = ResourceRField()

    _ko_list: list[str] = ListRField()

    def __init__(self, data: list[DataFrame] = None, ko_list: list[str] = None):
        super().__init__()
        self._simulations = []

        if not ko_list:
            ko_list = []

        if not isinstance(ko_list, list):
            raise BadRequestException(
                "The ko list must be an instance of list")
        self._ko_list = ko_list

        if data:
            for i, current_data in enumerate(data):
                flux_df = current_data["fluxes"]
                invalid_ko_ids = current_data["invalid_ko_ids"]
                flux_table = Table(data=flux_df)
                flux_table.name = self._create_flux_table_name(ko_list[i])
                flux_table.add_technical_info(TechnicalInfo(
                    key="invalid_ko_ids", value=f"{invalid_ko_ids}"))
                self.add_resource(flux_table)

        self._set_technical_info()

    def _create_flux_table_name(self, ko_id):
        slug_id = StringHelper.slugify(ko_id, snakefy=True, to_lower=False)
        return f"{self.FLUX_TABLE_NAME} - {slug_id}"

    # -- G --

    def get_simulations(self):
        """ Get simulations """
        return self._simulations

    def get_flux_table(self, ko_id) -> Table:
        """ Get the flux table """
        name = self._create_flux_table_name(ko_id)
        return self.get_resource(name)

    def get_flux_dataframe(self, ko_id) -> DataFrame:
        """ Get the flux table """
        name = self._create_flux_table_name(ko_id)
        return self.get_resource(name).get_data()

    def get_ko_ids(self) -> list[str]:
        """ Get the ids of the knock-outed reactions """
        return self._ko_list

    # -- S --

    def set_simulations(self, simulations: list):
        """ Set simulations """
        if not isinstance(simulations, list):
            raise BadRequestException("The simulations must be a list")
        self._simulations = simulations

    def _set_technical_info(self):
        pass

    @view(view_type=BarPlotView, human_name='KO Barplots', short_description='View KOA results as 2D-bar plots',
          specs=ConfigSpecs({
              "flux_names":
              ListParam(
                  human_name="Flux names",
                  short_description="List of fluxes to plot. Set 'biomass' to plot biomass reaction flux.")}))
    def view_as_bar_plot(self, params: ConfigParams) -> BarPlotView:
        """
        View one or several columns as 2D-bar plots
        """

        flux_names: list = params.get_value("flux_names")

        for flux_name in flux_names:
            values = []
            for ko_id in self.get_ko_ids():
                value = self.get_flux_dataframe(ko_id).at[flux_name, "value"]
                values.append(value)

            barplot_view = BarPlotView()
            barplot_view.add_series(
                y=values
            )
        barplot_view.x_tick_labels = self.get_ko_ids()
        barplot_view.x_label = "KO simulations"
        barplot_view.y_label = "flux"

        return barplot_view
