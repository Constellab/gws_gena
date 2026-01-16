

import pandas as pd
from gws_core import (
    BadRequestException,
    ResourceSet,
    Table,
    TechnicalInfo,
    TypingStyle,
    resource_decorator,
)
from pandas import DataFrame
from scipy import stats

from .fba_optimize_result import FBAOptimizeResult


@resource_decorator("FBAResult", human_name="FBA result", short_description="Flux Balance Analysis Result", hide=True,
                    style=TypingStyle.material_icon(material_icon_name='assessment', background_color='#FFC300'))
class FBAResult(ResourceSet):
    """
    FBAResult class.

    A resource set object containing the result tables of a flux balance analysis.
    """

    FLUX_TABLE_NAME = "Flux table"
    SV_TABLE_NAME = "SV table"

    _default_zero_flux_threshold = 0.05

    def __init__(self, flux_dataframe: DataFrame = None, sv_dataframe: DataFrame = None):
        super().__init__()

        if flux_dataframe is not None:
            # add flux table
            flux_table = Table(flux_dataframe)
            flux_table.name = self.FLUX_TABLE_NAME
            self.add_resource(flux_table)

        if sv_dataframe is not None:
            # add sv table
            sv_table = Table(sv_dataframe)
            sv_table.name = self.SV_TABLE_NAME
            self.add_resource(sv_table)
            self._set_technical_info()

    # -- C --

    def compute_zero_flux_threshold(self) -> (float, float):
        """ Compute the zero-flux threshold """
        data = self.get_sv_dataframe()
        value = data["value"]
        try:
            if value.shape[0] >= 20:
                _, p = stats.normaltest(value)
                return 3.0 * value.std(), p
            else:
                return self._default_zero_flux_threshold, None
        except Exception as _:
            return self._default_zero_flux_threshold, None

    # -- G --

    def get_sv_table(self):
        """ Get the SV table """
        return self.get_resource(self.SV_TABLE_NAME)

    def get_flux_table(self):
        """ Get the flux table """
        return self.get_resource(self.FLUX_TABLE_NAME)

    # def get_biomass_flux_dataframe(self) -> DataFrame:
    #     """ Get the biomass flux """
    #     t = []
    #     for net in self.get_twin().networks.values():
    #         rxn = net.get_biomass_reaction()
    #         flat_id = net.flatten_reaction_id(rxn)
    #         data = self.get_fluxes_dataframe()
    #         t.append(data.loc[[flat_id], :])
    #     return pd.concat(t)

    def get_flux_dataframe_by_reaction_ids(self, reaction_ids: list | str) -> DataFrame:
        """ Get flux values by reaction ids """
        if isinstance(reaction_ids, str):
            reaction_ids = [reaction_ids]
        if not isinstance(reaction_ids, list):
            raise BadRequestException("A str or a list of str is required")
        data = self.get_fluxes_dataframe()
        return data.loc[reaction_ids, :]

    def get_sv_by_compound_ids(self, compound_ids: list | str) -> DataFrame:
        """ Get SV values by compound ids """
        if isinstance(compound_ids, str):
            compound_ids = [compound_ids]
        if not isinstance(compound_ids, list):
            raise BadRequestException("A str or a list of str is required")
        data = self.get_sv_dataframe()
        return data.loc[compound_ids, :]

    def get_fluxes_dataframe(self) -> DataFrame:
        """ Get fluxes as dataframe """
        return self.get_flux_table().get_data()

    def get_sv_dataframe(self) -> DataFrame:
        """ Get SV as dataframe """
        return self.get_sv_table().get_data()

    def _set_technical_info(self):
        value, pval = self.compute_zero_flux_threshold()
        self.add_technical_info(TechnicalInfo(key="zero_flux_threshold", value=value))
        self.add_technical_info(TechnicalInfo(key="zero_flux_pvalue", value=pval))
        sv_table = self.get_sv_table()
        sv_table.add_technical_info(TechnicalInfo(key="zero_flux_threshold", value=value))
        sv_table.add_technical_info(TechnicalInfo(key="zero_flux_pvalue", value=pval))

    @classmethod
    def from_optimized_result(cls, optimized_result: FBAOptimizeResult) -> 'FBAResult':
        flux_dataframe = cls._create_fluxes_dataframe(optimized_result)
        sv_dataframe = cls._create_sv_dataframe(optimized_result)

        return FBAResult(flux_dataframe, sv_dataframe)

    @classmethod
    def _create_fluxes_dataframe(cls, res: FBAOptimizeResult) -> DataFrame:
        value = DataFrame(data=res.x, index=res.x_names, columns=["value"])
        if res.xmin is None:
            lower_bound = DataFrame(data=res.x, index=res.x_names, columns=["lower_bound"])
        else:
            lower_bound = DataFrame(data=res.xmin, index=res.x_names, columns=["lower_bound"])

        if res.xmax is None:
            upper_bound = DataFrame(data=res.x, index=res.x_names, columns=["upper_bound"])
        else:
            upper_bound = DataFrame(data=res.xmax, index=res.x_names, columns=["upper_bound"])

        data = pd.concat([value, lower_bound, upper_bound], axis=1)
        return data

    @classmethod
    def _create_sv_dataframe(cls, res: FBAOptimizeResult) -> DataFrame:
        data = DataFrame(data=res.constraints, index=res.constraint_names, columns=["value"])
        return data
