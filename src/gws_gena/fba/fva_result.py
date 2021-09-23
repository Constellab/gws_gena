# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas as pd
from pandas import DataFrame
from scipy.optimize import OptimizeResult as SciPyOptimizeResult

from gws_core import resource_decorator
from .fba_result import FBAResult
from .fba import OptimizeResult

@resource_decorator("FVAResult")
class FVAResult(FBAResult):
    """
    FVAResult class
    """

    def render__fluxes__as_table(self) -> DataFrame:
        res: OptimizeResult = self.optimize_result
        val = DataFrame(data=res.x, index=res.x_names, columns=["value"])
        lb = DataFrame(data=res.xmin, index=res.x_names, columns=["lower_bound"])
        ub = DataFrame(data=res.xmax, index=res.x_names, columns=["upper_bound"])
        return pd.concat([val, lb, ub], axis=1)
    
    def render__sv__as_table(self) -> DataFrame:
        res: OptimizeResult = self.optimize_result
        df = DataFrame(data=res.constraints, index=res.constraint_names, columns=["value"])
        return df
