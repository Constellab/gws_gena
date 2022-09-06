# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Union

import pandas as pd
from gws_core import (BadRequestException, ListRField, Resource,
                      ResourceRField, ResourceSet, SerializableObject,
                      SerializableRField, Table, TechnicalInfo,
                      resource_decorator)
from pandas import DataFrame
from scipy import stats

from ..network.network import Network
from ..network.reaction.reaction import Reaction
from ..network.typing.pathway_typing import ReactionPathwayDict
from ..twin.flat_twin import FlatTwin
from ..twin.twin import Twin
from .fba_optimize_result import FBAOptimizeResult


@resource_decorator("FBAResult", human_name="FBA result", short_description="Flux Balance Analysis Result", hide=True)
class FBAResult(ResourceSet):
    """
    FBAResult class.

    A resource set object containing the result tables of a flux balance analysis.
    """

    FLUX_TABLE_NAME = "Flux table"
    SV_TABLE_NAME = "SV table"

    _twin: Twin = ResourceRField()
    _simulations = ListRField()
    _optimize_result = SerializableRField(FBAOptimizeResult)  # DictRField(default_value={})
    _default_zero_flux_threshold = 0.05

    def __init__(self, twin: Twin = None, optimize_result: FBAOptimizeResult = None):
        super().__init__()
        if twin is None:
            self._simulations = []
            self._optimize_result = FBAOptimizeResult()
        else:
            if not isinstance(twin, Twin):
                raise BadRequestException("A twin is required")

            self._twin = twin
            self._optimize_result = optimize_result

            # add flux table
            flux_table = Table(data=self._create_fluxes_dataframe())
            flux_table.name = self.FLUX_TABLE_NAME
            self.add_resource(flux_table)

            # add sv table
            sv_table = Table(data=self._create_sv_dataframe())
            sv_table.name = self.SV_TABLE_NAME
            self.add_resource(sv_table)

            self._set_technical_info()

    # -- C --

    def compute_zero_flux_threshold(self) -> (float, float):
        """ Compute the zero-flux threshold """
        data = self._create_sv_dataframe()
        value = data["value"]
        try:
            if value.shape[0] >= 20:
                _, p = stats.normaltest(value)
                return 3.0 * value.std(), p
            else:
                return self._default_zero_flux_threshold, None
        except Exception as _:
            return self._default_zero_flux_threshold, None

    # -- C --

    def _create_fluxes_dataframe(self) -> DataFrame:
        res: FBAOptimizeResult = self._optimize_result
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

    def _create_pathways_dataframe(self) -> DataFrame:
        res: FBAOptimizeResult = self._optimize_result
        kegg_pw = []
        brenda_pw = []
        metacyc_pw = []
        if isinstance(self._twin, FlatTwin):
            flat_twin: FlatTwin = self._twin
        else:
            flat_twin: FlatTwin = self._twin.flatten()

        net: Network = flat_twin.get_flat_network()
        rxn: Reaction
        pathways: ReactionPathwayDict
        for rxn_id in res.x_names:
            if rxn_id in net.reactions.get_elements():
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
        data = pd.concat([brenda_pw, kegg_pw, metacyc_pw], axis=1)
        return data

    def _create_fluxes_and_pathways_dataframe(self) -> DataFrame:
        return pd.concat([self._create_fluxes_dataframe(), self._create_pathways_dataframe()], axis=1)

    def _create_sv_dataframe(self) -> DataFrame:
        res: FBAOptimizeResult = self._optimize_result
        data = DataFrame(data=res.constraints, index=res.constraint_names, columns=["value"])
        return data

    # -- G --

    def get_simulations(self):
        """ Get simulations """
        return self._simulations

    def get_twin(self):
        """ Get the digital twin """
        return self._twin

    def get_sv_table(self):
        """ Get the SV table """
        return self.get_resource(self.SV_TABLE_NAME)

    def get_flux_table(self):
        """ Get the flux table """
        return self.get_resource(self.FLUX_TABLE_NAME)

    def get_biomass_flux_dataframe(self) -> DataFrame:
        """ Get the biomass flux """
        t = []
        for net in self.get_twin().networks.values():
            rxn = net.get_biomass_reaction()
            flat_id = net.flatten_reaction_id(rxn)
            data = self.get_fluxes_dataframe()
            t.append(data.loc[[flat_id], :])
        return pd.concat(t)

    def get_flux_dataframe_by_reaction_ids(self, reaction_ids: Union[List, str]) -> DataFrame:
        """ Get flux values by reaction ids """
        if isinstance(reaction_ids, str):
            reaction_ids = [reaction_ids]
        if not isinstance(reaction_ids, list):
            raise BadRequestException("A str or a list ofstr is required")
        data = self.get_fluxes_dataframe()
        return data.loc[reaction_ids, :]

    def get_sv_by_compound_ids(self, compound_ids: Union[List, str]) -> DataFrame:
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

    def get_fluxes_and_pathways_dataframe(self):
        """ Get fluxes and pathways as dataframe """
        return self._create_fluxes_and_pathways_dataframe()

    def get_sv_dataframe(self) -> DataFrame:
        """ Get SV as dataframe """
        return self.get_sv_table().get_data()

    # -- S --

    def set_simulations(self, simulations: list):
        """ Set simulations """
        if not isinstance(simulations, list):
            raise BadRequestException("The simulations must be a list")
        self._simulations = simulations

    def _set_technical_info(self):
        value, pval = self.compute_zero_flux_threshold()
        self.add_technical_info(TechnicalInfo(key="zero_flux_threshold", value=value))
        self.add_technical_info(TechnicalInfo(key="zero_flux_pvalue", value=pval))
        for resource in self.get_resources().values():
            resource.add_technical_info(TechnicalInfo(key="zero_flux_threshold", value=value))
            resource.add_technical_info(TechnicalInfo(key="zero_flux_pvalue", value=pval))
