# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas as pd
from gws_core import ConfigParams, Table, resource_decorator
from pandas import DataFrame
from scipy.optimize import OptimizeResult as SciPyOptimizeResult

from .fba_result import FBAResult, OptimizeResult


@resource_decorator("FVAResult", human_name="FVA", short_description="Flux variability Analysis Result")
class FVAResult(FBAResult):
    """
    FVAResult class
    """

    pass
