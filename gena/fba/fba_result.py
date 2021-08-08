# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas as pd
from pandas import DataFrame
import numpy
import re
from scipy import stats

from gws.resource import Resource
from ..biomodel.biomodel import BioModel

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

class FBAResult(Resource):
    """
    FBAResult class
    """
    _annotated_bio = None
    _default_zero_flux_threshold = 0.01

    def __init__(self, *args, biomodel: BioModel=None, optimize_result: OptimizeResult = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.kv_store['optimize_result'] = optimize_result
        self.add_related_model(relation_name="biomodel", related_model=biomodel)

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
        res: OptimizeResult = self.kv_store['optimize_result']
        val = DataFrame(data=res.x, index=res.x_names, columns=["value"])
        lb = DataFrame(data=res.x, index=res.x_names, columns=["lower_bound"])
        ub = DataFrame(data=res.x, index=res.x_names, columns=["upper_bound"])
        return pd.concat([val, lb, ub], axis=1)

    def render__sv__as_table(self) -> DataFrame:
        res: OptimizeResult = self.kv_store['optimize_result']
        df = DataFrame(data=res.constraints, index=res.constraint_names, columns=["value"])
        return df

    def render__total_abs_flux__as_table(self) -> DataFrame:
        if not self._annotated_bio:
            from ..helper.biomodel_annotator_helper import BioModelAnnotatorHelper
            bio: BioModel = self.get_related_model(relation_name="biomodel")
            self._annotated_bio: BioModel = BioModelAnnotatorHelper.annotate(bio, self)
        net = list(self._annotated_bio.networks.values())[0]
        return net.render__total_abs_flux__as_table()

    def render__annotated_biomodel__as_json(self) -> dict:
        if not self._annotated_bio:
            from ..helper.biomodel_annotator_helper import BioModelAnnotatorHelper
            bio: BioModel = self.get_related_model(relation_name="biomodel")
            self._annotated_bio: BioModel = BioModelAnnotatorHelper.annotate(bio, self)
        return self._annotated_bio.to_json(shallow=False)