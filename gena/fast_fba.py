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
import cvxpy as cp

from gws.model import Resource, Process
from gws.logger import Error

from .base_fba import AbstractFBAResult
from .biomodel import BioModel, FlatBioModel
from .network import Network
from .context import Context
from .service.biomodel_service import BioModelService

from scipy import stats

class OptimizeResult:
    """
    OptimizeResult class.

    Simple proxy to SciPy OptimizeResult
    """
    def __init__(self, res:SciPyOptimizeResult, x_names: List[str], con_names: List[str]):
        self.x = res.x
        self.xmin = None
        self.xmax = None
        self.x_names = x_names
        self.con = res.con
        self.con_names = con_names
        self.fun = res.fun
        self.ni = res.nit
        self.message = res.message
        self.success = res.success
        self.status = res.status

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
        df = DataFrame(data=res.con, index=res.con_names, columns=["value"])
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
        "least_energy": {"type": bool, "default": True, "Description": "Search for minimal flux values satisfying the problem"},
        "fluxes_to_maximize": {"type": list, "default": [], "Description": "The fluxes to maximize"},
        "fluxes_to_minimize": {"type": list, "default": [], "Description": "The fluxes to minimize"},
        "solver": {"type": str, "default": "highs", "allowed_values": ["highs-ds", "highs-ipm", "highs", "interior-point"], "Description": "The optimization solver"}
    }

    async def task(self):
        self.progress_bar.set_value(1, message="Creating problem ...")
        bio = self.input["biomodel"]
        method = self.get_param("solver")
        least_energy = self.get_param("least_energy")
        fluxes_to_maximize = self.get_param("fluxes_to_maximize")
        fluxes_to_minimize = self.get_param("fluxes_to_minimize")

        c, A_eq, b_eq, bounds = self.build_problem(
            bio, 
            fluxes_to_maximize=fluxes_to_maximize, 
            fluxes_to_minimize=fluxes_to_minimize
        )

        self.progress_bar.set_value(2, message=f"Starting optimization with solver '{method}' ...")
        
        res: OptimizeResult = self.solve_scipy( 
            c, A_eq, b_eq, bounds, 
            least_energy=least_energy,
            method=method
        )
        #res: OptimizeResult = self.solve_cvxpy( c, A_eq, b_eq, bounds, least_energy=least_energy )

        self.progress_bar.set_value(95, message="Gather results ...")

        result = FastFBAResult(optimize_result = res)
        self.output["result"] = result

    @staticmethod
    def build_problem( bio, *, fluxes_to_maximize = [], fluxes_to_minimize = []):
        flat_bio: FlatBioModel = bio.flatten(as_biomodel=True)
        flat_net: Network = flat_bio.flat_network

        # reshape problem
        obsv = BioModelService.create_observation_matrices(flat_bio)
        C = obsv["C"]
        
        S_int = BioModelService.create_intracell_stoichiometric_matrix(flat_bio)

        Y_names = [ "v_"+s for s in C.index ]

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

        B = obsv["B"]
        y_b = B.loc[:, ["target"]]
        y_lb = B.loc[:, ["lb"]]
        y_ub = B.loc[:, ["ub"]]

        A_eq_left = pd.concat([S_int, C, Y_zeros], axis=0) #vert_concat
        A_eq_right = pd.concat([S_zeros, _Id_C, Id_Y], axis=0) #vert_concat
        A_eq = pd.concat([A_eq_left, A_eq_right], axis=1) #horz_concat

        b_zero_1 = DataFrame(data=np.zeros((S_int.shape[0], 1,)))
        b_zero_2 = DataFrame(data=np.zeros((C.shape[0], 1,)))
        b_zero_1.columns = y_b.columns
        b_zero_2.columns = y_b.columns
        b_eq = pd.concat([b_zero_1, b_zero_2, y_b], axis=0) #vert_concat
        b_eq.index = A_eq.index
 
        lb = pd.concat([v_lb, y_lb], axis=0) #vert_concat
        lb.index = A_eq.columns
        ub = pd.concat([v_ub, y_ub], axis=0) #vert_concat
        ub.index = A_eq.columns

        c = DataFrame( 
            index = lb.index,
            data = np.zeros( (lb.shape[0],1) )
        )

        for k in fluxes_to_minimize:
            tab = k.split(":")
            name = tab[0]
            weight = (tab[1] if len(tab) == 2 else 1.0)
            weight = -abs(float(weight))
            if math.isnan(weight) or weight == 0:
                raise Error("FastFBA", "build_problem", f"Invalid weight value '{tab[1]}'")

            if name == "biomass":
                biomass_rxn = flat_net.get_biomass_reaction()
                if biomass_rxn:
                    c.loc[ biomass_rxn.id, 0 ] = weight
                else:
                    raise Error("FastFBA", "build_problem", f"Reaction to minimize not found with id '{k}'")
            else:
                if name in c.index:
                    c.loc[name, 0] = weight
                else:
                    raise Error("FastFBA", "build_problem", f"Reaction to maximize not found with id '{k}'")

        for k in fluxes_to_maximize:
            tab = k.split(":")
            name = tab[0]
            weight = (tab[1] if len(tab) == 2 else -1.0)
            weight = -abs(float(weight))
            if math.isnan(weight) or weight == 0:
                raise Error("FastFBA", "build_problem", f"Invalid weight value '{tab[1]}'")

            if name == "biomass":
                biomass_rxn = flat_net.get_biomass_reaction()
                if biomass_rxn:
                    c.loc[ biomass_rxn.id, 0 ] = weight
                else:
                    raise Error("FastFBA", "build_problem", f"Reaction to maximize not found with id '{k}'")
            else:
                if name in c.index:
                    c.loc[name, 0] = weight
                else:
                    raise Error("FastFBA", "build_problem", f"Reaction to maximize not found with id '{k}'")

        lb = lb.to_numpy()
        ub = ub.to_numpy()

        bounds = []
        for i in range(lb.shape[0]):
            bounds.append((lb[i,0], ub[i,0]))

        return c, A_eq, b_eq, bounds
    
    # @staticmethod
    # def solve_cvxpy( c, A_eq, b_eq, bounds, *, least_energy=False ):
    #     c = c.to_numpy()
    #     A_eq = A_eq.to_numpy()
    #     b_eq = b_eq.to_numpy()

    #     n = A_eq.shape[0]
    #     m = A_eq.shape[1]
 
    #     x = cp.Variable(m)
    #     #c.shape = (m,1)
    #     b_eq.shape = (n,)

    #     lb = []
    #     ub = []
    #     for b in bounds:
    #         lb.append(b[0])
    #         ub.append(b[1])

    #     lb = np.ndarray((m,), buffer=np.array(lb))
    #     ub = np.ndarray((m,), buffer=np.array(ub))

    #     prob = cp.Problem(
    #         cp.Minimize(c.T@x), 
    #         [A_eq @ x == b_eq, x >= lb, x <= ub]
    #     )
    #     prob.solve()
    #     return prob

    @staticmethod
    def solve_scipy( c, A_eq, b_eq, bounds, *, least_energy=False, method="interior-point", x0=None) -> OptimizeResult:
        x_names = A_eq.columns
        con_names = A_eq.index

        if least_energy:
            # extend the problem 
            #1) add a set of flux to explcitely account for forward/backward fluxes
            #2) to set all flux values > 0
            #3) update vector c to mimize all flux values (excepted thoses given in the config)

            A_eq = pd.concat([A_eq, -A_eq], axis=1)
            c = pd.concat([c, -c], axis=0)

            new_bounds = []
            for b in bounds:
                lb = 0
                ub = b[1]
                new_bounds.append((lb, ub))

            for b in bounds:
                lb = 0
                ub = b[1]
                new_bounds.append((lb, ub))
            
            bounds = new_bounds

            for i in range(0, c.shape[1]):
                if c.iat[i,0] == 0.0:
                    c.iat[i,0] = 1/c.shape[0]  #scaling to balance these weights with fluxes to maxize/minimize

            res = linprog(
                c,
                A_eq=A_eq.to_numpy(),
                b_eq=b_eq.to_numpy(),
                bounds=bounds,
                method=method,
                x0=x0,
            )

            n = int(res.x.shape[0] / 2)
            res.x = res.x[:n] - res.x[n:]
        else:
            res = linprog(
                c,
                A_eq=A_eq.to_numpy(),
                b_eq=b_eq.to_numpy(),
                bounds=bounds,
                method=method,
                x0=x0
            )
        return OptimizeResult(res, x_names, con_names)