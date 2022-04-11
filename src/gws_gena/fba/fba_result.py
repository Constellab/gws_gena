# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union

import pandas as pd
from gws_core import (BadRequestException, Resource, ResourceRField,
                      ResourceSet, RField, Table, resource_decorator)
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


@resource_decorator("FBAResult", human_name="FBA result", short_description="Flux Balance Analysis Result", hide=True)
class FBAResult(ResourceSet):
    """
    FBAResult class
    """

    FLUX_TABLE_NAME = "Flux table"
    SV_TABLE_NAME = "SV table"

    _twin: Twin = ResourceRField()
    _optimize_result = RField(default_value=None)
    _default_zero_flux_threshold = 0.01

    def __init__(self, twin: Twin = None, optimize_result: OptimizeResult = None):
        super().__init__()
        if twin is not None:
            if not isinstance(twin, Twin):
                raise BadRequestException("A twin is required")

            self._optimize_result = optimize_result

            flux_table = Table(data=self._create_fluxes_dataframe())
            flux_table.name = self.FLUX_TABLE_NAME
            self.add_resource(flux_table)

            sv_table = Table(data=self._create_sv_dataframe())
            sv_table.name = self.SV_TABLE_NAME
            self.add_resource(sv_table)

            self._twin = twin

    # -- C --

    def compute_zero_flux_threshold(self) -> (float, float):
        data = self._create_sv_dataframe()
        val = data["value"]
        try:
            if val.shape[0] >= 20:
                _, p = stats.normaltest(val)
                if p < 0.05:
                    return 2.0 * val.std(), p
                else:
                    return self._default_zero_flux_threshold, None
            else:
                return self._default_zero_flux_threshold, None
        except Exception as _:
            return self._default_zero_flux_threshold, None

    # -- C --

    def _create_fluxes_dataframe(self) -> DataFrame:
        res: OptimizeResult = self._optimize_result
        val = DataFrame(data=res.x, index=res.x_names, columns=["value"])
        if res.xmin is None:
            lb = DataFrame(data=res.x, index=res.x_names, columns=["lower_bound"])
        else:
            lb = DataFrame(data=res.xmin, index=res.x_names, columns=["lower_bound"])
        if res.xmax is None:
            ub = DataFrame(data=res.x, index=res.x_names, columns=["upper_bound"])
        else:
            ub = DataFrame(data=res.xmax, index=res.x_names, columns=["upper_bound"])

        data = pd.concat([val, lb, ub], axis=1)
        return data

    def _create_pathways_dataframe(self) -> DataFrame:
        res: OptimizeResult = self._optimize_result

        kegg_pw = []
        brenda_pw = []
        metacyc_pw = []

        if isinstance(self._twin, FlatTwin):
            flat_twin: FlatTwin = self._twin
        else:
            flat_twin: FlatTwin = self._twin.flatten()

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
        data = pd.concat([brenda_pw, kegg_pw, metacyc_pw], axis=1)
        return data

    def _create_fluxes_and_pathways_dataframe(self) -> DataFrame:
        return pd.concat([self._create_fluxes_dataframe(), self._create_pathways_dataframe()], axis=1)

    def _create_sv_dataframe(self) -> DataFrame:
        res: OptimizeResult = self._optimize_result
        data = DataFrame(data=res.constraints, index=res.constraint_names, columns=["value"])
        return data

    # -- G --

    def get_twin(self):
        return self._twin

    def get_sv_table(self):
        return self.get_resource(self.SV_TABLE_NAME)

    def get_flux_table(self):
        return self.get_resource(self.FLUX_TABLE_NAME)

    def get_fluxes_by_reaction_ids(self, reaction_ids: Union[List, str]) -> DataFrame:
        if isinstance(reaction_ids, str):
            reaction_ids = [reaction_ids]
        if not isinstance(reaction_ids, list):
            raise BadRequestException("A str or a list of str is required")
        data = self.get_fluxes_dataframe()
        return data.loc[reaction_ids, :]

    def get_sv_by_compound_ids(self, compound_ids: Union[List, str]) -> DataFrame:
        if isinstance(compound_ids, str):
            compound_ids = [compound_ids]
        if not isinstance(compound_ids, list):
            raise BadRequestException("A str or a list of str is required")
        data = self.get_sv_dataframe()
        return data.loc[compound_ids, :]

    def get_fluxes_dataframe(self) -> DataFrame:
        return self.get_flux_table().get_data()

    def get_fluxes_and_pathways_dataframe(self):
        return self._create_fluxes_and_pathways_dataframe()

    def get_sv_dataframe(self) -> DataFrame:
        return self.get_sv_table().get_data()

    # -- V --
