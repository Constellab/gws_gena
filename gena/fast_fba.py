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
from scipy import stats
import numpy as np
import cvxpy as cp
import re

from gws.process import Process
from gws.logger import Logger
from gws.exception.bad_request_exception import BadRequestException

from .base_fba import AbstractFBAResult
from .biomodel import BioModel, FlatBioModel
from .network import Network
from .context import Context
from .compound import Compound
from .service.biomodel_service import BioModelService
from .helper.sink_helper import SinkHelper

class OptimizeResult:
    """
    OptimizeResult class.

    Simple proxy to SciPy OptimizeResult
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

class FastFBAResult(AbstractFBAResult):
    """
    FastFBAResult class
    """

    def __init__(self, *args, optimize_result: OptimizeResult = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.kv_store['optimize_result'] = optimize_result

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

class FastFBA(Process):
    """
    FastFBA class

    The flux analysis problem is shaped as follows:
    -----------------------------------------------
    min c' * v
    s.t.
        A_{ub} * v_{ub} = b_{ub}
        A_{eq} * v_{eq} = b_{eq}
        lb < v < ub

    With FBA, one has:
        S_{int} * v = 0
        v_{lb} < v < v_{ub}
    and
        C * v = y (<=> C * v - y = 0)
        y = y_b
        y_lb < y < y_ub 
    where 
        S_{int} is the intracellular stoichimetric matrix
        y is the vector of measurement, 
        y_b is the vector containing measured values
        y_{lb} is the vector containing lower bounds of measured values
        y_{ub} is the vector containing upper bounds of measured values

    Then, the problem is reshaped as follows:


             [ S_{int} |  0      ]           [  0  ]
             [ --------|------   ]           [ --- ]
    A_{eq} = [   C     | -Id_{C} ], b_{eq} = [  0  ]
             [---------|------   ]           [-----]
             [   0     |  Id_{Y} ]           [ y_b ]
    
         [  v  ]
    x =  [ --- ]
         [  y  ]
    
         [ v_{lb} ]        [ v_{ub} ]
    lb = [ ----   ],  ub = [ ----   ]
         [ y_{lb} ]        [ y_{ub} ]

    Id_{C} and Id_{Y} are identity matrices.
    """

    input_specs = { 'biomodel': (BioModel,) }
    output_specs = { 'result': (FastFBAResult,) }
    config_specs = {
        "fluxes_to_maximize": {"type": list, "default": [], "Description": "The fluxes to maximize"},
        "fluxes_to_minimize": {"type": list, "default": [], "Description": "The fluxes to minimize"},
        "solver": {"type": str, "default": "highs", "allowed_values": ["highs-ds", "highs-ipm", "highs", "interior-point", "quad"], "Description": "The optimization solver"},
        "fill_gaps_with_sinks": {"type": bool, "default": True, "Description": ""}
    }

    async def task(self):
        self.progress_bar.set_value(1, message="Creating problem ...")
        bio = self.input["biomodel"]
        method = self.get_param("solver")
        fluxes_to_maximize = self.get_param("fluxes_to_maximize")
        fluxes_to_minimize = self.get_param("fluxes_to_minimize")
        fill_gaps_with_sinks = self.get_param("fill_gaps_with_sinks")
        c, A_eq, b_eq, bounds = self.build_problem(
            bio, 
            fluxes_to_maximize=fluxes_to_maximize, 
            fluxes_to_minimize=fluxes_to_minimize,
            fill_gaps_with_sinks=fill_gaps_with_sinks
        )
        
        self.progress_bar.set_value(2, message=f"Starting optimization with solver '{method}' ...")
        if self.get_param("solver") == "quad":
            res: OptimizeResult = self.solve_cvxpy( 
                c, A_eq, b_eq, bounds
            )
        else:
            res: OptimizeResult = self.solve_scipy( 
                c, A_eq, b_eq, bounds,
                method=method
            )
        self.progress_bar.set_value(90, message=res.message)
        result = FastFBAResult(optimize_result = res)
        self.output["result"] = result

    # -- B --

    @classmethod
    def build_problem( cls, bio, *, fluxes_to_maximize = [], fluxes_to_minimize = [], fill_gaps_with_sinks=True):
        flat_bio: FlatBioModel = bio.flatten(as_biomodel=True)
        flat_net: Network = flat_bio.flat_network
        if fill_gaps_with_sinks:
            SinkHelper.fill_gaps_with_sinks(flat_net)
        
        # reshape problem
        obsv_matrix = BioModelService.create_observation_matrices(flat_bio)
        C = obsv_matrix["C"]
        b = obsv_matrix["b"]

        S_int = BioModelService.create_steady_stoichiometric_matrix(flat_bio)
        Y_names = [ "v_"+name for name in C.index ]
        S_zeros = DataFrame( 
            index = S_int.index,
            columns = Y_names,
            data=np.zeros((S_int.shape[0],C.shape[0],)) 
        )
        _Id_C = DataFrame( 
            index = C.index,
            columns = Y_names,
            data= - np.identity(C.shape[0])
        )
        Y_names = [ "v_"+s for s in C.index ]
        Y_zeros = DataFrame( 
            index = Y_names,
            columns = S_int.columns,
            data=np.zeros((C.shape[0],S_int.shape[1],)) 
        )
        Id_Y = DataFrame( 
            index = Y_names,
            columns = Y_names,
            data=np.identity(C.shape[0])
        )
        df = flat_net.get_reaction_bounds()
        v_lb = df.loc[:,["lb"]]
        v_ub = df.loc[:,["ub"]]
        y_b = b.loc[:, ["target"]]
        y_lb = b.loc[:, ["lb"]]
        y_ub = b.loc[:, ["ub"]]

        # A_eq
        A_eq_left = pd.concat([S_int, C, Y_zeros], axis=0) #vert_concat
        A_eq_right = pd.concat([S_zeros, _Id_C, Id_Y], axis=0) #vert_concat
        A_eq = pd.concat([A_eq_left, A_eq_right], axis=1) #horz_concat
        
        # b_eq
        b_zero_1 = DataFrame(data=np.zeros((S_int.shape[0], 1,)))
        b_zero_2 = DataFrame(data=np.zeros((C.shape[0], 1,)))
        b_zero_1.columns = y_b.columns
        b_zero_2.columns = y_b.columns
        b_eq = pd.concat([b_zero_1, b_zero_2, y_b], axis=0) #vert_concat
        b_eq.index = A_eq.index

        # lb and ub
        lb = pd.concat([v_lb, y_lb], axis=0) #vert_concat
        lb.index = A_eq.columns
        ub = pd.concat([v_ub, y_ub], axis=0) #vert_concat
        ub.index = A_eq.columns

        lb_numpy = lb.to_numpy()
        ub_numpy = ub.to_numpy()
        bounds = []
        for i in range(lb_numpy.shape[0]):
            bounds.append((lb_numpy[i,0], ub_numpy[i,0]))
        fluxes_to_minimize = cls.__expand_fluxes_by_names(fluxes_to_minimize, flat_net)
        fluxes_to_maximize = cls.__expand_fluxes_by_names(fluxes_to_maximize, flat_net)

        # vector c
        c = DataFrame( index = lb.index, data = np.zeros( (lb.shape[0],1) ) )
        c = cls.__upgrade_c_with_fluxes_to_min_max(c, flat_net, fluxes_to_minimize, direction="min")
        c = cls.__upgrade_c_with_fluxes_to_min_max(c, flat_net,fluxes_to_maximize, direction="max")
        #c = cls.__upgrade_c_with_sink_fluxes_to_min(c, flat_net)

        return c, A_eq, b_eq, bounds
    
    # -- C --

    # -- E --

    @classmethod
    def __expand_fluxes_by_names(cls, fluxes_to_minmax, flat_net):
        expanded_fluxes_to_minmax = []
        list_of_rxn_names = list(flat_net.reactions.keys())
        for k in fluxes_to_minmax:
            tab = k.split(":")
            rxn_name = tab[0]
            weight = tab[1] if len(tab) == 2 else '1.0'
            if rxn_name == "biomass":
                biomass_rxn = flat_net.get_biomass_reaction()
                if biomass_rxn:
                    expanded_fluxes_to_minmax.append( biomass_rxn.id + ":" + weight )
                else:
                    raise BadRequestException(f"Reaction to minimize not found with id '{k}'")
            else:
                #is_reg = re.match(r"[^0-9a-zA-Z_\-]", rxn_name)
                #if is_reg:
                if "*" in rxn_name:
                    for tmp_rxn_name in list_of_rxn_names:
                        if re.match(rxn_name, tmp_rxn_name):
                            expanded_fluxes_to_minmax.append( tmp_rxn_name+":"+weight )
                else:
                    if rxn_name in list_of_rxn_names:
                        expanded_fluxes_to_minmax.append( rxn_name+":"+weight )
                    else:
                        raise BadRequestException(f"Reaction to maximize not found with id '{k}'")
        return list(set(expanded_fluxes_to_minmax))

    # -- S --

    @staticmethod
    def solve_cvxpy( c, A_eq, b_eq, bounds):
        x_names = A_eq.columns
        con_names = A_eq.index

        A_eq = A_eq.to_numpy()
        b_eq = b_eq.to_numpy()
        n = A_eq.shape[0]
        m = A_eq.shape[1]
        x = cp.Variable(m)
        b_eq.shape = (n,)
        lb = []
        ub = []
        for b in bounds:
            lb.append(b[0])
            ub.append(b[1])
        lb = np.ndarray((m,), buffer=np.array(lb))
        ub = np.ndarray((m,), buffer=np.array(ub))

        has_sink = False
        P = np.zeros((m, m))
        for i in range(0,m):
            rxn_name = c.index[i]
            is_sink_rxn = rxn_name.endswith("_sink")
            if is_sink_rxn:
                P[i][i] = 1.0
                has_sink = True

        c = c.to_numpy()
        if has_sink:
            prob = cp.Problem(
                cp.Minimize( (1/2)*cp.quad_form(x, P) + c.T@x ),
                [A_eq @ x == b_eq, x >= lb, x <= ub]
            )
        else:
            prob = cp.Problem(
                cp.Minimize(c.T@x), 
                [A_eq @ x == b_eq, x >= lb, x <= ub]
            )
        prob.solve(max_iter=50000)

        res = dict(
            x = x.value,
            xmin = None,
            xmax = None,
            x_names = x_names,
            constraints = prob.constraints[0].residual,
            constraint_names = con_names,
            niter = prob.solver_stats.num_iters,
            message = "",
            success = prob.status == "optimal",
            status = prob.status
        )
        Logger.progress(f"Optimization status: {prob.status}")
        return OptimizeResult(res)

    @staticmethod
    def solve_scipy( c, A_eq, b_eq, bounds, *, method="interior-point") -> OptimizeResult:
        x_names = A_eq.columns
        con_names = A_eq.index
        has_sink = False
        for rxn_name in c.index:
            if rxn_name.endswith("_sink"):
                has_sink = True
                break
        
        if has_sink:
            sink_idx = []
            none_sink_idx = []
            sink_names = []
            extended_bounds = []
            m = A_eq.shape[1]
            for i in range(0,m):
                rxn_name = c.index[i]
                is_sink_rxn = rxn_name.endswith("_sink")
                bnd = bounds[i]
                if is_sink_rxn:
                    sink_idx.append(i)
                    sink_names.append(rxn_name)
                    c.loc[rxn_name, 0] = 1.0
                    extended_bounds.append((0, bnd[1]))
                    #extended_bounds.append(bnd)
                else:
                    none_sink_idx.append(i)
                    extended_bounds.append(bnd)
                    
            A_sink = A_eq.loc[:, sink_names]
            c_sink = c.loc[sink_names, 0] #DataFrame(data=np.ones((len(sink_idx), 1,)))
            A_eq = pd.concat([A_eq, -A_sink], axis=1)
            c = pd.concat([c, c_sink], axis=0)
            extended_bounds = [ *extended_bounds, *[extended_bounds[k] for k in sink_idx] ]
     
            res = linprog(
                c,
                A_eq=A_eq.to_numpy(),
                b_eq=b_eq.to_numpy(),
                bounds=extended_bounds,
                method=method
            )
            if res.status == 0:
                res.x[sink_idx] = res.x[sink_idx] - res.x[m:] #compute sink balance
                res.x = res.x[:m]
        else:
            res = linprog(
                c,
                A_eq=A_eq.to_numpy(),
                b_eq=b_eq.to_numpy(),
                bounds=bounds,
                method=method,
            )

        res = dict(
            x = res.x,
            xmin = None,
            xmax = None,
            x_names = x_names,
            constraints = res.con,
            constraint_names = con_names,
            niter = res.nit,
            message = res.message,
            success = res.success,
            status = res.status
        )
        Logger.progress(res["message"])
        return OptimizeResult(res)

    # -- U --

    @classmethod
    def __upgrade_c_with_fluxes_to_min_max(cls, c, flat_net, fluxes_to_minmax, direction):
        for k in fluxes_to_minmax:
            tab = k.split(":")
            rxn_name = tab[0]
            weight = float(tab[1] if len(tab) == 2 else 1.0)
            weight = abs(weight) if direction == "min" else -abs(weight)
            if math.isnan(weight) or weight == 0:
                raise BadRequestException(f"Invalid weight value '{tab[1]}'")
            if rxn_name == "biomass":
                biomass_rxn = flat_net.get_biomass_reaction()
                if biomass_rxn and (biomass_rxn.id in c.index):
                    c.loc[ biomass_rxn.id, 0 ] = weight
                else:
                    raise BadRequestException(f"Reaction to minimize not found with id '{k}'")
            else:
                if (rxn_name in flat_net.reactions) and (rxn_name in c.index):
                    c.loc[rxn_name, 0] = weight
                else:
                    raise BadRequestException(f"Reaction to maximize not found with id '{k}'")
        return c
