# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import abc
import json
import pandas as pd
from pandas import DataFrame
from scipy import stats

from gws_core import File
from gws_core import Resource, resource_decorator

from ..twin.twin import Twin
from .fba_result import FBAResult as BaseFBAResult, OptimizeResult

@resource_decorator("DeprecFBAResult")
class DeprecFBAResult(File, BaseFBAResult):
    _content = None
    _default_zero_flux_threshold = 0.01

    def __init__(self, *args, twin: Twin=None, optimize_result: OptimizeResult = None, **kwargs):
        File.__init__(self, *args, **kwargs)
        BaseFBAResult.__init__(self, *args, twin=twin, optimize_result=optimize_result, **kwargs)

    # -- A --

    # -- C --

    @property
    def content(self)->dict:
        if not self._content:
            self._content = json.loads(self.read())
        return self._content
    
    # -- K --

    @property
    def sv(self)->dict:
        return self.content["problem"]["sv"]
    
    @property
    def solutions(self)->dict:
        return self.content["problem"]["solutions"]
    
    @property
    def solver_success(self)->dict:
        return self.content["problem"]["solver_success"]
    
    # -- V --
    
    def render__sv_distrib__as_table(self, only_sucess: bool = True) -> DataFrame:
        df = DataFrame(
            self.sv["data"], 
            index=self.sv["row_names"], 
            columns=self.sv["col_names"]
        )
        if only_sucess:
            success = self.render__solver_success__as_table()
            success_columns = df.columns[success.iloc[0,:]]
            df = df[ success_columns ]
        return df

    def render__sv__as_table(self, only_sucess: bool = True) -> DataFrame:
        df = self.render__sv_ranges__as_table(only_sucess = True)
        df = df[:, ["mean"]]
        df.columns = ["value"]
        return df

    def render__sv_ranges__as_table(self, only_sucess: bool = True) -> DataFrame:
        df = self.render__sv_distrib__as_table(only_sucess=only_sucess)
        Q1 = df.quantile(q=0.25, axis=1)
        Q2 = df.quantile(q=0.5, axis=1)
        Q3 = df.quantile(q=0.75, axis=1)
        df = pd.concat( 
            [ 
                df.mean(axis=1), 
                df.std(axis=1), 
                df.min(axis=1), 
                df.max(axis=1),
                Q2, Q3 - Q1, Q1, Q3
            ],
            axis=1 
        )
        df.columns = [ "mean", "std", "min", "max", "Q2", "IQR", "Q1", "Q3" ]
        #df = df.sort_values(by=["std"])
        return df

    def render__solver_success__as_table(self) -> DataFrame:
        df = DataFrame(
            self.solver_success["data"], 
            index=self.solver_success["row_names"], 
            columns=self.solver_success["col_names"]
        )
        return df == 1.0

    def render__fluxes__as_table(self) -> DataFrame:
        fluxes:DataFrame = self.render__flux_ranges__as_table()
        val:DataFrame = fluxes.loc[:, ["mean"]]
        std:DataFrame = fluxes.loc[:, ["std"]].fillna(0)
        val.columns = ["data"]
        std.columns = ["data"]
        lb = val.sub(std, axis=1)
        ub = val.add(std, axis=1)
        df = pd.concat([val, lb, ub], axis=1)
        df.columns = ["value", "lower_bound", "upper_bound"]
        return df

    def render__flux_ranges__as_table(self, only_sucess: bool = True) -> DataFrame:
        df = self.render__flux_distrib__as_table(only_sucess=only_sucess)
        Q1 = df.quantile(q=0.25, axis=1)
        Q2 = df.quantile(q=0.5, axis=1)
        Q3 = df.quantile(q=0.75, axis=1)
        df = pd.concat( 
            [ 
                df.mean(axis=1), 
                df.std(axis=1), 
                df.min(axis=1), 
                df.max(axis=1),
                Q2, Q3 - Q1, Q1, Q3
            ],
            axis=1 
        )
        df.columns = [ "mean", "std", "min", "max", "Q2", "IQR", "Q1", "Q3" ]
        #df = df.sort_values(by=["std"])
        return df
    
    def render__flux_distrib__as_table(self, only_sucess: bool = True) -> DataFrame:
        df = DataFrame(
            self.solutions["data"], 
            index=self.solutions["row_names"], 
            columns=self.solutions["col_names"]
        )
        if only_sucess:
            success = self.render__solver_success__as_table()
            success_columns = df.columns[success.iloc[0,:]]
            df = df[ success_columns ]
        return df
  