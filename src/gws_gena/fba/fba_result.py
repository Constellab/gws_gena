# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas as pd
from pandas import DataFrame
import numpy
import re
from scipy import stats

from gws_core import Resource, resource_decorator, RField, DictRField
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

@resource_decorator("FBAResult")
class FBAResult(Resource):
    """
    FBAResult class
    """

    twin_data = DictRField()
    optimize_result = RField(default_value=None)

    _annotated_twin = None
    _default_zero_flux_threshold = 0.01

    def __init__(self, *args, twin: Twin=None, optimize_result: OptimizeResult = None, **kwargs):
        super().__init__(*args, **kwargs)
        if twin is not None:
            self.twin_data = twin.dumps(deep=True)
            self.optimize_result = optimize_result
            

    def get_related_twin(self):
        return Twin.loads(self.twin_data)
    # -- C --

    def compute_zero_flux_threshold(self) -> (float, float):
        df = self.render__sv__as_table()
        val = df["value"]
        try:
            if val.shape[0] >= 20:
                _,p = stats.normaltest(val)
                if p < 0.05:
                    return 2.0 * val.std(), p
                else:
                    return self._default_zero_flux_threshold, None
            else:
                return self._default_zero_flux_threshold, None
        except:
            return self._default_zero_flux_threshold, None

    # -- R --

    def render__fluxes__as_table(self) -> DataFrame:
        res: OptimizeResult = self.optimize_result
        val = DataFrame(data=res.x, index=res.x_names, columns=["value"])
        lb = DataFrame(data=res.x, index=res.x_names, columns=["lower_bound"])
        ub = DataFrame(data=res.x, index=res.x_names, columns=["upper_bound"])
        return pd.concat([val, lb, ub], axis=1)

    def render__sv__as_table(self) -> DataFrame:
        res: OptimizeResult = self.optimize_result
        df = DataFrame(data=res.constraints, index=res.constraint_names, columns=["value"])
        return df

    def render__total_abs_flux__as_table(self) -> DataFrame:
        if not self._annotated_twin:
            from ..helper.twin_annotator_helper import TwinAnnotatorHelper
            twin: Twin = self.get_related_twin()
            self._annotated_twin: Twin = TwinAnnotatorHelper.annotate(twin, self)
        net = list(self._annotated_twin.networks.values())[0]
        return net.render__total_abs_flux__as_table()

    def render__annotated_twin__as_json(self) -> dict:
        if not self._annotated_twin:
            from ..helper.twin_annotator_helper import TwinAnnotatorHelper
            twin: Twin = self.get_related_twin()
            self._annotated_twin: Twin = TwinAnnotatorHelper.annotate(twin, self)
        return self._annotated_twin.to_json(deep=True)