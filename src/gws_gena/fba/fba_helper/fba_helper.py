# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math
import re

import cvxpy as cp
import numpy as np
import pandas as pd
from gws_core import BadRequestException, Logger
from pandas import DataFrame
from scipy.optimize import linprog

from ...network.network import Network
from ...twin.flat_twin import FlatTwin
from ...twin.helper.twin_helper import TwinHelper
from ...twin.twin import Twin
from ..fba_result import FBAResult, FBAOptimizeResult
from ...helper.base_helper import BaseHelper

class FBAHelper(BaseHelper):

    """
    FBA helper class

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

    __CVXPY_MAX_ITER = 100000
    __CVXPY_SOLVER_PRIORITY = [cp.OSQP, cp.ECOS]

    def run(self, twin: Twin, solver, fluxes_to_maximize=None, fluxes_to_minimize=None, biomass_optimization=None,
            fill_gaps_with_sinks: bool = None, ignore_cofactors: bool = None, relax_qssa: bool = None,
            qssa_relaxation_strength: float = None) -> FBAResult:
        cls = type(self)
        self.log_info_message(message="Creating problem ...")
        if relax_qssa and solver != "quad":
            self.log_info_message(message=f"Change solver to '{solver}' for constrain relaxation.")
            solver = "quad"

        if not isinstance(twin, Twin):
            raise BadRequestException("A twin is required")

        if isinstance(twin, FlatTwin):
            flat_twin = twin
        else:
            flat_twin: FlatTwin = twin.flatten()

        c, A_eq, b_eq, bounds = cls.build_problem(
            flat_twin,
            biomass_optimization=biomass_optimization,
            fluxes_to_maximize=fluxes_to_maximize,
            fluxes_to_minimize=fluxes_to_minimize,
            fill_gaps_with_sinks=fill_gaps_with_sinks,
            ignore_cofactors=ignore_cofactors,
        )
        self.update_progress_value(2, message=f"Starting optimization with solver '{solver}' ...")
        if solver == "quad":
            res, _ = cls.solve_cvxpy(
                c, A_eq, b_eq, bounds,
                relax_qssa=relax_qssa,
                qssa_relaxation_strength=qssa_relaxation_strength
            )
        else:
            res: FBAOptimizeResult = cls.solve_scipy(
                c, A_eq, b_eq, bounds,
                solver=solver
            )
        self.update_progress_value(90, message=res.message)
        result = FBAResult(twin=twin, optimize_result=res)
        return result

    @classmethod
    def build_problem(
            cls, flat_twin: FlatTwin, biomass_optimization=None, fluxes_to_maximize: list = None,
            fluxes_to_minimize: list = None,
            fill_gaps_with_sinks: bool = True, ignore_cofactors: bool = False):

        if fluxes_to_maximize is None:
            fluxes_to_maximize = []
        if fluxes_to_minimize is None:
            fluxes_to_minimize = []
        if not isinstance(flat_twin, FlatTwin):
            raise BadRequestException("A flat twin is required")

        if biomass_optimization:
            fat_net = flat_twin.get_flat_network()
            biomass_rxn = fat_net.get_biomass_reaction()
            if biomass_optimization == "maximize":
                fluxes_to_maximize.append(biomass_rxn.id)
                fluxes_to_maximize = list(set(fluxes_to_maximize))
            elif biomass_optimization == "minimize":
                fluxes_to_minimize.append(biomass_rxn.id)
                fluxes_to_minimize = list(set(fluxes_to_minimize))

        flat_net: Network = flat_twin.get_flat_network()
        # if fill_gaps_with_sinks:
        #     SinkHelper.fill_gaps_with_sinks(flat_net)

        # reshape problem
        obsv_matrix = TwinHelper.create_observation_matrices(flat_twin)
        C = obsv_matrix["C"]
        b = obsv_matrix["b"]

        S_int = TwinHelper.create_steady_stoichiometric_matrix(flat_twin, ignore_cofactors=ignore_cofactors)
        Y_names = C.index
        S_zeros = DataFrame(
            index=S_int.index,
            columns=Y_names,
            data=np.zeros((S_int.shape[0], C.shape[0],))
        )
        _Id_C = DataFrame(
            index=C.index,
            columns=Y_names,
            data=- np.identity(C.shape[0])
        )

        Y_obs_names = [s+"_obsv" for s in Y_names]
        Y_zeros = DataFrame(
            index=Y_obs_names,
            columns=S_int.columns,
            data=np.zeros((C.shape[0], S_int.shape[1],))
        )
        Id_Y = DataFrame(
            index=Y_zeros.index,
            columns=Y_names,
            data=np.identity(C.shape[0])
        )

        df = flat_net.get_reaction_bounds()
        int_flux_lb = df.loc[:, ["lb"]]
        int_flux_ub = df.loc[:, ["ub"]]

        out_flux_target = b.loc[:, ["target"]]
        out_flux_lb = b.loc[:, ["lb"]]
        out_flux_ub = b.loc[:, ["ub"]]
        beq_confidence_score = b.loc[:, ["confidence_score"]]

        # A_eq
        A_eq_left = pd.concat([S_int, C, Y_zeros], axis=0)  # vert_concat
        A_eq_right = pd.concat([S_zeros, _Id_C, Id_Y], axis=0)  # vert_concat
        A_eq = pd.concat([A_eq_left, A_eq_right], axis=1)  # horz_concat

        # b_eq
        b_zero_1 = DataFrame(data=np.zeros((S_int.shape[0], 1,)))
        b_zero_2 = DataFrame(data=np.zeros((C.shape[0], 1,)))
        b_zero_1.columns = out_flux_target.columns
        b_zero_2.columns = out_flux_target.columns
        b_eq = pd.concat([b_zero_1, b_zero_2, out_flux_target], axis=0)  # vert_concat
        b_eq.index = A_eq.index

        # lb and ub
        lb = pd.concat([int_flux_lb, out_flux_lb], axis=0)  # vert_concat
        lb.index = A_eq.columns
        ub = pd.concat([int_flux_ub, out_flux_ub], axis=0)  # vert_concat
        ub.index = A_eq.columns

        lb_numpy = lb.to_numpy()
        ub_numpy = ub.to_numpy()
        bounds = []
        for i in range(lb_numpy.shape[0]):
            bounds.append([lb_numpy[i, 0], ub_numpy[i, 0]])
        fluxes_to_minimize = cls._expand_fluxes_by_names(fluxes_to_minimize, flat_net)
        fluxes_to_maximize = cls._expand_fluxes_by_names(fluxes_to_maximize, flat_net)

        # vector c
        c = DataFrame(index=lb.index, data=np.zeros((lb.shape[0], 1)))
        c = cls.__upgrade_c_with_fluxes_to_min_max(c, flat_net, fluxes_to_minimize, direction="min")
        c = cls.__upgrade_c_with_fluxes_to_min_max(c, flat_net, fluxes_to_maximize, direction="max")
        A_eq, b_eq = cls.__upgrade_Aeq_beq_with_output_coefficient_score(A_eq, b_eq, beq_confidence_score)

        return c, A_eq, b_eq, bounds

    # -- C --

    # -- E --

    @classmethod
    def _expand_fluxes_by_names(cls, fluxes_to_minmax, flat_net):
        expanded_fluxes_to_minmax = []
        if fluxes_to_minmax is None:
            return []
        list_of_rxn_names = list(flat_net.reactions.keys())
        for k in fluxes_to_minmax:
            tab = k.split(":")
            rxn_name = tab[0]
            weight = tab[1] if len(tab) == 2 else '1.0'
            if rxn_name.lower() == "biomass":
                biomass_rxn = flat_net.get_biomass_reaction()
                if biomass_rxn:
                    expanded_fluxes_to_minmax.append(biomass_rxn.id + ":" + weight)
                else:
                    raise BadRequestException("The biomass reaction is not found")
            else:
                if rxn_name in list_of_rxn_names:
                    expanded_fluxes_to_minmax.append(rxn_name+":"+weight)
                else:
                    raise BadRequestException(f"Invalid reactions to maximize. No reaction found with id '{k}'")
        return list(set(expanded_fluxes_to_minmax))

    # -- S --

    @classmethod
    def __do_solve_cvxpy_prob(cls, prob, verbose=False):

        def ___do_solve_cvxpy_prob_i(i, prob, has_switched=False, verbose=False):
            current_solver = cls.__CVXPY_SOLVER_PRIORITY[i]
            if current_solver == cp.OSQP:
                params = {"max_iter": cls.__CVXPY_MAX_ITER}
                msg = "ECOS failed. Switched to OSQP."
            else:
                params = {"max_iters": cls.__CVXPY_MAX_ITER}
                msg = "OSQP failed. Switched to ECOS."
            if has_switched:
                Logger.progress(msg)
            prob.solve(solver=current_solver, **params, verbose=verbose)

        has_switched = False
        try:
            ___do_solve_cvxpy_prob_i(0, prob, verbose=verbose)
        except:
            has_switched = True
            ___do_solve_cvxpy_prob_i(1, prob, has_switched=True, verbose=verbose)
        finally:
            is_success = (prob.status == "optimal")
            if not is_success and not has_switched:
                has_switched = True
                ___do_solve_cvxpy_prob_i(1, prob, has_switched=True, verbose=verbose)

    @classmethod
    def solve_cvxpy(cls, c, A_eq, b_eq, bounds, relax_qssa, qssa_relaxation_strength, verbose=False):
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
        for i in range(0, m):
            rxn_name = c.index[i]
            is_sink_rxn = rxn_name.endswith("_sink")
            if is_sink_rxn:
                P[i][i] = 1.0
                has_sink = True

        # b_eq param
        b_eq_par = cp.Parameter(shape=(n,), value=b_eq)

        # c param
        c = c.to_numpy()
        c.shape = (m,)
        c_par = cp.Parameter(shape=(m,), value=c)

        # bound param
        ub_par = cp.Parameter(shape=(m,), value=ub)
        lb_par = cp.Parameter(shape=(m,), value=lb)

        if relax_qssa:
            if qssa_relaxation_strength is None:
                qssa_relaxation_strength = 1
            qssa_cost = qssa_relaxation_strength * cp.sum_squares(A_eq @ x - b_eq_par)
            if has_sink:
                prob = cp.Problem(
                    cp.Minimize((1/2)*cp.quad_form(x, P) + c_par.T@x + qssa_cost),
                    [
                        x >= lb_par,
                        x <= ub_par
                    ],
                )
            else:
                # regularizer = cp.sum_squares(x)
                prob = cp.Problem(
                    cp.Minimize(c_par.T@x + qssa_cost),  # + 0.0*regularizer,
                    [
                        x >= lb_par,
                        x <= ub_par
                    ]
                )
                cls.__do_solve_cvxpy_prob(prob, verbose=verbose)
            con = A_eq @ x.value - b_eq
        else:
            if has_sink:
                prob = cp.Problem(
                    cp.Minimize((1/2)*cp.quad_form(x, P) + c_par.T@x),
                    [
                        A_eq @ x == b_eq_par,
                        x >= lb_par,
                        x <= ub_par
                    ]
                )
                cls.__do_solve_cvxpy_prob(prob, verbose=verbose)
            else:
                prob = cp.Problem(
                    cp.Minimize(c_par.T@x),
                    [
                        A_eq @ x == b_eq_par,
                        x >= lb_par,
                        x <= ub_par
                    ]
                )
                prob.solve(verbose=verbose)
            con = prob.constraints[0].residual

        res = dict(
            x=x.value,
            xmin=None,
            xmax=None,
            x_names=x_names,
            constraints=con,
            constraint_names=con_names,
            niter=(prob.solver_stats.num_iters if prob.solver_stats else None),
            message="",
            success=prob.status == "optimal",
            status=prob.status
        )

        warm_solver = dict(x=x, c_par=c_par, b_eq_par=b_eq_par, lb_par=lb_par, ub_par=ub_par, prob=prob)
        if verbose:
            Logger.progress(f"Optimization status: {prob.status}")
        return FBAOptimizeResult(res), warm_solver

    @classmethod
    def solve_cvxpy_using_warm_solver(
            cls, warm_solver, c_update=None, b_eq_update=None, lb_update=None, ub_update=None):
        x: cp.Variable = warm_solver["x"]
        c_par = warm_solver["c_par"]
        b_eq_par = warm_solver["b_eq_par"]
        lb_par = warm_solver["lb_par"]
        ub_par = warm_solver["ub_par"]
        prob = warm_solver["prob"]

        if c_update is not None:
            if isinstance(c_update, DataFrame):
                c_update = c_update.to_numpy()
                c_update.shape = c_par.shape
            c_par.value = c_update
        if b_eq_update is not None:
            if isinstance(b_eq_update, DataFrame):
                b_eq_update = b_eq_update.to_numpy()
                b_eq_update.shape = b_eq_par.shape
            b_eq_par.value = b_eq_update
        if lb_update is not None:
            if isinstance(lb_update, DataFrame):
                lb_update = lb_update.to_numpy()
                lb_update.shape = b_eq_par.shape
            lb_par.value = lb_update
        if ub_update is not None:
            if isinstance(ub_update, DataFrame):
                ub_update = ub_update.to_numpy()
                ub_update.shape = b_eq_par.shape
            ub_par.value = ub_update

        cls.__do_solve_cvxpy_prob(prob)
        return x.value

    @classmethod
    def solve_scipy(cls, c, A_eq, b_eq, bounds, *, solver="interior-point", verbose=False) -> FBAOptimizeResult:
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
            for i in range(0, m):
                rxn_name = c.index[i]
                is_sink_rxn = rxn_name.endswith("_sink")
                bnd = bounds[i]
                if is_sink_rxn:
                    sink_idx.append(i)
                    sink_names.append(rxn_name)
                    c.loc[rxn_name, 0] = 1.0
                    extended_bounds.append([0, bnd[1]])
                else:
                    none_sink_idx.append(i)
                    extended_bounds.append(bnd)

            A_sink = A_eq.loc[:, sink_names]
            c_sink = c.loc[sink_names, 0]  # DataFrame(data=np.ones((len(sink_idx), 1,)))
            A_eq = pd.concat([A_eq, -A_sink], axis=1)
            c = pd.concat([c, c_sink], axis=0)
            extended_bounds = [*extended_bounds, *[extended_bounds[k] for k in sink_idx]]

            res = linprog(
                c,
                A_eq=A_eq.to_numpy(),
                b_eq=b_eq.to_numpy(),
                bounds=extended_bounds,
                method=solver
            )
            if res.status == 0:
                res.x[sink_idx] = res.x[sink_idx] - res.x[m:]  # compute sink balance
                res.x = res.x[:m]
        else:
            res = linprog(
                c,
                A_eq=A_eq.to_numpy(),
                b_eq=b_eq.to_numpy(),
                bounds=bounds,
                method=solver,
            )

        res = dict(
            x=res.x,
            xmin=None,
            xmax=None,
            x_names=x_names,
            constraints=res.con,
            constraint_names=con_names,
            niter=res.nit,
            message=res.message,
            success=res.success,
            status=res.status
        )
        if verbose:
            Logger.progress(res["message"])
        return FBAOptimizeResult(res)

    # -- U --

    @classmethod
    def __upgrade_Aeq_beq_with_output_coefficient_score(cls, A_eq, b_eq, beq_confidence_score):
        for i in range(0, beq_confidence_score.shape[0]):
            name = beq_confidence_score.index[i]
            name_obs = name + "_obsv"
            score = abs(beq_confidence_score.iloc[i, 0])
            b_eq.loc[name_obs, :] = score * b_eq.loc[name_obs, :]
            A_eq.loc[name_obs, :] = score * A_eq.loc[name_obs, :]
        return A_eq, b_eq

    @classmethod
    def __upgrade_c_with_fluxes_to_min_max(cls, c, flat_net, fluxes_to_minmax, direction):
        if fluxes_to_minmax is None:
            fluxes_to_minmax = []

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
                    c.loc[biomass_rxn.id, 0] = weight
                else:
                    raise BadRequestException(f"Reaction to minimize not found with id '{k}'")
            else:
                if (rxn_name in flat_net.reactions) and (rxn_name in c.index):
                    c.loc[rxn_name, 0] = weight
                else:
                    raise BadRequestException(f"Reaction to maximize not found with id '{k}'")
        return c
