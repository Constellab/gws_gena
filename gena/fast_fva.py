# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import math
import pandas as pd
from typing import List
from pandas import DataFrame
from scipy.optimize import linprog
from scipy.optimize import OptimizeResult as SciPyOptimizeResult
import numpy as np

from gws.model import Resource, Process
from gws.logger import Error

from .base_fba import AbstractFBAResult
from .fast_fba import FastFBA, OptimizeResult

from .biomodel import BioModel, FlatBioModel
from .network import Network
from .context import Context
from .service.biomodel_service import BioModelService

from scipy import stats

class FastFVAResult(AbstractFBAResult):
    """
    FastFBAResult class
    """

    def __init__(self, *args, optimize_result: OptimizeResult = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.kv_store['optimize_result'] = optimize_result

    def render__fluxes__as_table(self) -> DataFrame:
        res: OptimizeResult = self.kv_store['optimize_result']

        val = DataFrame(data=res.x, index=res.x_names, columns=["value"])
        lb = DataFrame(data=res.xmin, index=res.x_names, columns=["lower_bound"])
        ub = DataFrame(data=res.xmax, index=res.x_names, columns=["upper_bound"])
        return pd.concat([val, lb, ub], axis=1)

    def render__sv__as_table(self) -> DataFrame:
        res: OptimizeResult = self.kv_store['optimize_result']
        df = DataFrame(data=res.con, index=res.con_names, columns=["value"])
        return df


class FastFVA(Process):
    """
    FastFVA class

    The fast flux variability analyzer. 
    It is based on the work of [1] using the revised simplex optimization algorithm during variability analysis.


    [1] Steinn Gudmundsson & Ines Thiele, Computationally efficient flux variability analysis, 
        BMC Bioinformatics, volume 11, Article number: 489 (2010),
        https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-11-489
    """

    input_specs = { 'biomodel': (BioModel,) }
    output_specs = { 'result': (FastFVAResult,) }
    config_specs = {
        "least_energy": {"type": bool, "default": True, "Description": "Search for minimal flux values satisfying the problem"},
        "fluxes_to_maximize": {"type": list, "default": [], "Description": "The fluxes to maximize"},
        "fluxes_to_minimize": {"type": list, "default": [], "Description": "The fluxes to minimize"},
        "solver": {"type": str, "default": "highs", "allowed_values": ["highs-ds", "highs-ipm", "highs", "interior-point"], "Description": "The optimization solver"}
    }

    async def task(self):
        self.progress_bar.add_message(message="Creating problem ...")
        bio = self.input["biomodel"]
        method = self.get_param("solver")
        least_energy = self.get_param("least_energy")
        fluxes_to_maximize = self.get_param("fluxes_to_maximize")
        fluxes_to_minimize = self.get_param("fluxes_to_minimize")

        c, A_eq, b_eq, bounds = FastFBA.build_problem(
            bio, 
            fluxes_to_maximize=fluxes_to_maximize, 
            fluxes_to_minimize=fluxes_to_minimize
        )

        self.progress_bar.add_message(message=f"Starting optimization with solver '{method}' ...")

        res: OptimizeResult = FastFBA.solve_scipy( 
            c, A_eq, b_eq, bounds, 
            least_energy=least_energy,
            method=method
        )

        self.progress_bar.add_message(message=res.message)
        if res.status != 0:
            raise Error("FastFVA", "task", res.message)

        self.progress_bar.add_message(message=f"Peforming variability analysis around the optimal value using solver {method} ...")
 
        x0 = res.x
        n = x0.shape[0]
        xmin = np.zeros(x0.shape)
        xmax = np.zeros(x0.shape)
        
        for i in range(0,n):
            print(f" flux {i+1}/{n} ...")
            self.progress_bar.set_value(i, message=f" flux {i+1}/{n} ...")

            cf = DataFrame(data=np.zeros(c.shape), index=c.index)

            is_minmax = (c.index[i] in fluxes_to_maximize) or (c.index[i] in fluxes_to_minimize)
            if is_minmax:
                xmin[i] = res.x[i]
                xmax[i] = res.x[i]
            else:
                # min
                cf.iloc[i,0] = 1

                res_fva = FastFBA.solve_scipy( 
                    cf, A_eq, b_eq, bounds, 
                    least_energy=least_energy,
                    method=method,
                    x0 = x0
                )
                xmin[i] = res_fva.x[i]

                #max
                cf.iloc[i,0] = -1
                res_fva = FastFBA.solve_scipy( 
                    cf, A_eq, b_eq, bounds, 
                    least_energy=least_energy,
                    method=method,
                    x0 = x0
                )
                xmax[i] = res_fva.x[i]

        res.xmin = xmin
        res.xmax = xmax

        result = FastFVAResult(optimize_result=res)
        self.output["result"] = result