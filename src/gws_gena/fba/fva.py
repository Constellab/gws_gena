# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame
import numpy as np
import multiprocessing
from joblib import Parallel, delayed
from copy import deepcopy
import cvxpy as cp

from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs
from gws_core import BadRequestException, ListParam, StrParam, BoolParam
from gws_core import Logger

from .fba_helper.fba_helper import FBAHelper
from .fba_result import OptimizeResult
from .fva_result import FVAResult
from ..twin.twin import Twin, FlatTwin

def _do_parallel_loop(kwargs):
    i=kwargs["i"]
    c=kwargs["c"]
    A_eq=kwargs["A_eq"]
    b_eq=kwargs["b_eq"]
    bounds=kwargs["bounds"]
    x0=kwargs["x0"]
    indexes_of_fluxes_to_minimize=kwargs["indexes_of_fluxes_to_minimize"]
    indexes_of_fluxes_to_maximize=kwargs["indexes_of_fluxes_to_maximize"]
    step=kwargs["step"]
    m=kwargs["m"]
    solver=kwargs["solver"]
    relax_qssa=kwargs["relax_qssa"]

    if (i % step) == 0:
        Logger.progress(f" flux {i+1}/{m} ...")
        #self.progress_bar.set_value(i, message=f" flux {i+1}/{m} ...")

    cf = DataFrame(data=np.zeros(c.shape), index=c.index)
    if (i in indexes_of_fluxes_to_minimize) or (i in indexes_of_fluxes_to_maximize):
        xmin = x0[i]
        xmax = x0[i]
    else:
        bounds = deepcopy(bounds)
        for k in indexes_of_fluxes_to_minimize:
            bounds[k][0] = x0[k]*0.975
            bounds[k][1] = x0[k]*1.025

        for k in indexes_of_fluxes_to_maximize:
            bounds[k][0] = x0[k]*0.975
            bounds[k][1] = x0[k]*1.025

        # min
        cf.iloc[i,0] = 1.0
        if solver == "quad":
            res_fva, _ = FBAHelper.solve_cvxpy(
                cf, A_eq, b_eq, bounds,
                relax_qssa=relax_qssa,
                verbose=False
            )
        else:
            res_fva: OptimizeResult = FBAHelper.solve_scipy(
                cf, A_eq, b_eq, bounds,
                solver=solver
            )
        xmin = res_fva.x[i]

        # max
        cf.iloc[i,0] = -1.0
        if solver == "quad":
            res_fva, _ = FBAHelper.solve_cvxpy(
                cf, A_eq, b_eq, bounds,
                relax_qssa=relax_qssa,
                verbose=False
            )
        else:
            res_fva: OptimizeResult = FBAHelper.solve_scipy(
                cf, A_eq, b_eq, bounds,
                solver=solver
            )
        xmax = res_fva.x[i]
    return xmin, xmax

@task_decorator("FVA")
class FVA(Task):
    """
    FVA class

    Performs flux variability analysis based on the work of [1].

    [1] Steinn Gudmundsson & Ines Thiele, Computationally efficient flux variability analysis,
        BMC Bioinformatics, volume 11, Article number: 489 (2010),
        https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-11-489
    """

    input_specs = { 'twin': (Twin,) }
    output_specs = { 'result': (FVAResult,) }
    config_specs = {
        "fluxes_to_maximize": ListParam(default_value="[]", human_name="Fluxes to maximize", short_description="The list of fluxes to maximize"),
        "fluxes_to_minimize": ListParam(default_value="[]", human_name="Fluxes to minimize", short_description="The list of fluxes to minimize"),
        "solver": StrParam(default_value="highs", visibility="protected", allowed_values=["quad", "highs-ds", "highs-ipm", "highs", "interior-point"], human_name="Solver", short_description="The optimization solver"),
        "fill_gaps_with_sinks": BoolParam(default_value=False, human_name="Fill gaps with sinks", short_description="True to fill gaps using sink reaction. False otherwise"),
        "relax_qssa": BoolParam(default_value=False, human_name="Relax QSSA", short_description="True to relaxing the quasi-steady state constrain (quad solver is used). False otherwise."),
        "ignore_cofactors": BoolParam(default_value=False, human_name="Ignore cofactors", short_description="True to ignore cofactors quasi-steady state for cofactors. False otherwise.")
    }
    __CVXPY_MAX_ITER = 100000

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        self.log_info_message(message="Creating problem ...")
        twin = inputs["twin"]
        solver = params["solver"]
        relax_qssa = params["relax_qssa"]
        fill_gaps_with_sinks = params["fill_gaps_with_sinks"]
        fluxes_to_maximize = params["fluxes_to_maximize"]
        fluxes_to_minimize = params["fluxes_to_minimize"]
        ignore_cofactors = params["ignore_cofactors"]

        if relax_qssa and solver != "quad":
            self.log_info_message(message=f"Change solver to '{solver}' for constrain relaxation.")
            solver = "quad"

        if isinstance(twin, FlatTwin):
            flat_twin = twin
        else:
            flat_twin: FlatTwin = twin.flatten()

        c, A_eq, b_eq, bounds = FBAHelper.build_problem(
            flat_twin,
            fluxes_to_maximize=fluxes_to_maximize,
            fluxes_to_minimize=fluxes_to_minimize,
            fill_gaps_with_sinks=fill_gaps_with_sinks,
            ignore_cofactors=ignore_cofactors
        )

        self.log_info_message(message=f"Starting optimization with solver '{solver}' ...")
        if solver == "quad":
            res, warm_solver = FBAHelper.solve_cvxpy(
                c, A_eq, b_eq, bounds,
                relax_qssa=relax_qssa,
                verbose=False
            )
        else:
            res: OptimizeResult = FBAHelper.solve_scipy(
                c, A_eq, b_eq, bounds,
                solver=solver
            )
        self.log_info_message(message=res.message)
        if not res.success:
            raise BadRequestException(f"Convergence error. Optimization message: '{res.message}'")

        self.log_info_message(message=f"Peforming variability analysis around the optimal value using solver '{solver}' ...")
        x0 = res.x
        m = x0.shape[0]
        step = max(1, int(m/10)) # plot only 10 iterations on screen

        if solver == "quad":
            xmin, xmax = self.__solve_with_cvxpy_using_warm_solver( warm_solver,
                                                                    c, A_eq, b_eq, bounds, x0,
                                                                    fluxes_to_maximize,
                                                                    fluxes_to_minimize,
                                                                    step, m, solver, relax_qssa)
            # xmin, xmax = self.__solve_with_parloop( c, A_eq, b_eq, bounds, x0,
            #                                         fluxes_to_maximize,
            #                                         fluxes_to_minimize,
            #                                         step, m, solver, relax_qssa)
        else:
            xmin, xmax = self.__solve_with_parloop( c, A_eq, b_eq, bounds, x0,
                                                    fluxes_to_maximize,
                                                    fluxes_to_minimize,
                                                    step, m, solver, relax_qssa)
        res.xmin = xmin
        res.xmax = xmax
        result = FVAResult(twin=twin, optimize_result=res)
        return {"result": result}

    @staticmethod
    def __solve_with_parloop(   c, A_eq, b_eq, bounds, x0,
                                fluxes_to_maximize,
                                fluxes_to_minimize,
                                step, m, solver, relax_qssa):

        max_idx = [ c.index.get_loc(name.split(":")[0]) for name in fluxes_to_maximize]
        min_idx = [ c.index.get_loc(name.split(":")[0]) for name in fluxes_to_minimize]
        # run parallel optimization
        Logger.progress("Open parallel pool for each flux.")
        pool = multiprocessing.Pool()
        params = [ ]
        for i in range(0,m):
            params.append( dict(
                    i=i,
                    c=c,
                    A_eq=A_eq,
                    b_eq=b_eq,
                    bounds=bounds,
                    x0=x0,
                    indexes_of_fluxes_to_minimize=min_idx,
                    indexes_of_fluxes_to_maximize=max_idx,
                    step=step,
                    m=m,
                    solver=solver,
                    relax_qssa=relax_qssa
                )
            )
        result = pool.map(_do_parallel_loop, params)
        # gather results
        xmin = np.zeros(x0.shape)
        xmax = np.zeros(x0.shape)
        for i in range(0,m):
            xmin[i] = result[i][0]
            xmax[i] = result[i][1]
        return xmin, xmax

    @staticmethod
    def __solve_with_cvxpy_using_warm_solver( warm_solver,
                            c, A_eq, b_eq, bounds, x0,
                            fluxes_to_maximize,
                            fluxes_to_minimize,
                            step, m, solver, relax_qssa):

        max_idx = [ c.index.get_loc(name.split(":")[0]) for name in fluxes_to_maximize]
        min_idx = [ c.index.get_loc(name.split(":")[0]) for name in fluxes_to_minimize]
        lb = warm_solver["lb_par"]
        ub = warm_solver["ub_par"]
        for k in max_idx:
            lb.value[k] = x0[k]*0.975
            ub.value[k] = x0[k]*1.025
        for k in min_idx:
            lb.value[k] = x0[k]*0.975
            ub.value[k] = x0[k]*1.025

        xmin = np.zeros(x0.shape)
        xmax = np.zeros(x0.shape)
        x = warm_solver["x"]
        c_par = warm_solver["c_par"]
        prob = warm_solver["prob"]
        for i in range(0,m):
            if (i % step) == 0:
                Logger.progress(f" flux {i+1}/{m} ...")
                #self.progress_bar.set_value(i, message=f" flux {i+1}/{m} ...")
            cf = DataFrame(data=np.zeros(c.shape), index=c.index)
            if (i in max_idx) or (i in min_idx):
                xmin[i] = x0[i]
                xmax[i] = x0[i]
            else:
                # min
                cf.iloc[i,0] = 1.0
                c_update = cf.to_numpy()
                c_update.shape = c_par.shape
                c_par.value = c_update
                try:
                    prob.solve(solver=cp.OSQP, max_iter=FVA.__CVXPY_MAX_ITER, verbose=False)
                except:
                    Logger.progress("OSQP failed. Switch to ECOS solver")
                    prob.solve(solver=cp.ECOS, max_iters=FVA.__CVXPY_MAX_ITER, verbose=False)
                xmin[i] = x.value[i]

                # max
                cf.iloc[i,0] = -1.0
                c_update = cf.to_numpy()
                c_update.shape = c_par.shape
                c_par.value = c_update
                try:
                    prob.solve(solver=cp.OSQP, max_iter=FVA.__CVXPY_MAX_ITER, verbose=False)
                except:
                    Logger.progress("OSQP failed. Switch to ECOS solver")
                    prob.solve(solver=cp.ECOS, max_iters=FVA.__CVXPY_MAX_ITER, verbose=False)
                xmax[i] = x.value[i]
        return xmin, xmax