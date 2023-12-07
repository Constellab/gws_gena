# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import multiprocessing
from copy import deepcopy

import cvxpy as cp
import numpy as np
from gws_core import (BadRequestException, ConfigParams, InputSpec, InputSpecs,
                      Logger, OutputSpec, OutputSpecs, Task, TaskInputs,
                      TaskOutputs, task_decorator)
# from joblib import Parallel, delayed
from pandas import DataFrame

from ..fba.fba import FBA
from ..fba.fba_helper.fba_helper import FBAHelper
from ..fba.fba_result import FBAOptimizeResult
from ..network.network import Network
from ..twin.flat_twin import FlatTwin
from ..twin.helper.twin_annotator_helper import TwinAnnotatorHelper
from ..twin.twin import Twin
from .fva_result import FVAResult


def _do_parallel_loop(kwargs):
    i = kwargs["i"]
    c = kwargs["c"]
    A_eq = kwargs["A_eq"]
    b_eq = kwargs["b_eq"]
    bounds = kwargs["bounds"]
    c_out = kwargs["c_out"]
    x0 = kwargs["x0"]
    indexes_of_fluxes_to_minimize = kwargs["indexes_of_fluxes_to_minimize"]
    indexes_of_fluxes_to_maximize = kwargs["indexes_of_fluxes_to_maximize"]
    step = kwargs["step"]
    m = kwargs["m"]
    solver = kwargs["solver"]
    relax_qssa = kwargs["relax_qssa"]
    qssa_relaxation_strength = kwargs["qssa_relaxation_strength"]
    parsimony_strength = kwargs["parsimony_strength"]

    if (i % step) == 0:
        Logger.progress(f" flux {i+1}/{m} ...")
        # self.progress_bar.set_value(i, message=f" flux {i+1}/{m} ...")

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
        cf.iloc[i, 0] = 1.0
        if solver == "quad":
            res_fva, _ = FBAHelper.solve_cvxpy(
                cf, A_eq, b_eq, bounds, c_out,
                relax_qssa=relax_qssa,
                qssa_relaxation_strength=qssa_relaxation_strength,
                parsimony_strength=parsimony_strength,
                verbose=False
            )
        else:
            res_fva: FBAOptimizeResult = FBAHelper.solve_scipy(
                cf, A_eq, b_eq, bounds, c_out,
                solver=solver
            )
        xmin = res_fva.x[i]

        # max
        cf.iloc[i, 0] = -1.0
        if solver == "quad":
            res_fva, _ = FBAHelper.solve_cvxpy(
                cf, A_eq, b_eq, bounds, c_out,
                relax_qssa=relax_qssa,
                qssa_relaxation_strength=qssa_relaxation_strength,
                parsimony_strength=parsimony_strength,
                verbose=False
            )
        else:
            res_fva: FBAOptimizeResult = FBAHelper.solve_scipy(
                cf, A_eq, b_eq, bounds, c_out,
                solver=solver
            )
        xmax = res_fva.x[i]
    return xmin, xmax


@task_decorator("FVA", human_name="FVA", short_description="Flux variability analysis")
class FVA(Task):
    """
    FVA class

    Performs flux variability analysis. It is based on the paper of (Gudmundsson and Thiele, Bioinformatics 2010).

    See also:

    > Steinn Gudmundsson & Ines Thiele, Computationally efficient flux variability analysis,
    BMC Bioinformatics, volume 11, Article number: 489 (2010),
    https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-11-489
    """

    input_specs = InputSpecs({'twin': InputSpec(Twin, human_name="Digital twin",
                             short_description="The digital twin to analyze")})
    output_specs = OutputSpecs({
        'twin': OutputSpec(Twin, human_name="Simulated digital twin", short_description="The simulated digital twin"),
        'fva_result': OutputSpec(FVAResult, human_name="FVA result table", short_description="The FVA result tables")
    })
    config_specs = {
        **FBA.config_specs
    }
    __CVXPY_MAX_ITER = 100000

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        self.log_info_message(message="Creating problem ...")
        twin = inputs["twin"]
        solver = params["solver"]
        relax_qssa = params["relax_qssa"]
        fluxes_to_maximize = params["fluxes_to_maximize"]
        fluxes_to_minimize = params["fluxes_to_minimize"]
        qssa_relaxation_strength = params["qssa_relaxation_strength"]
        parsimony_strength = 0.0  # params["parsimony_strength"]

        if relax_qssa and solver != "quad":
            self.log_info_message(message=f"Change solver to '{solver}' for constrain relaxation.")
            solver = "quad"

        if isinstance(twin, FlatTwin):
            flat_twin = twin
        else:
            flat_twin: FlatTwin = twin.flatten()

        c, A_eq, b_eq, bounds, c_out = FBAHelper.build_problem(
            flat_twin,
            fluxes_to_maximize=fluxes_to_maximize,
            fluxes_to_minimize=fluxes_to_minimize
        )

        self.log_info_message(message=f"Starting optimization with solver '{solver}' ...")
        if solver == "quad":
            res, warm_solver = FBAHelper.solve_cvxpy(
                c, A_eq, b_eq, bounds, c_out,
                relax_qssa=relax_qssa,
                qssa_relaxation_strength=qssa_relaxation_strength,
                parsimony_strength=parsimony_strength,
                verbose=False
            )
        else:
            res: FBAOptimizeResult = FBAHelper.solve_scipy(
                c, A_eq, b_eq, bounds, c_out,
                solver=solver
            )
        self.log_info_message(message=res.message)
        if not res.success:
            raise BadRequestException(f"Convergence error. Optimization message: '{res.message}'")

        self.log_info_message(
            message=f"Peforming variability analysis around the optimal value using solver '{solver}' ...")
        x0 = res.x
        m = x0.shape[0]
        step = max(1, int(m/10))  # plot only 10 iterations on screen

        flat_net: Network = flat_twin.get_flat_network()
        fluxes_to_minimize = FBAHelper._expand_fluxes_by_names(fluxes_to_minimize, flat_net)
        fluxes_to_maximize = FBAHelper._expand_fluxes_by_names(fluxes_to_maximize, flat_net)

        if solver == "quad":
            xmin, xmax = self.__solve_with_cvxpy_using_warm_solver(warm_solver,
                                                                   c, x0,
                                                                   fluxes_to_maximize,
                                                                   fluxes_to_minimize,
                                                                   step, m)
        else:
            xmin, xmax = self.__solve_with_parloop(
                c, A_eq, b_eq, bounds, c_out, x0, fluxes_to_maximize,
                fluxes_to_minimize, step, m, solver, relax_qssa,
                qssa_relaxation_strength, parsimony_strength)
        res.xmin = xmin
        res.xmax = xmax
        fva_result = FVAResult(twin=twin, optimize_result=res)

        # annotate twin
        helper = TwinAnnotatorHelper()
        helper.attach_task(self)
        twin = helper.annotate_from_fva_result(twin, fva_result)

        return {
            "fva_result": fva_result,
            "twin": twin
        }

    @staticmethod
    def __solve_with_parloop(c, A_eq, b_eq, bounds, c_out, x0,
                             fluxes_to_maximize,
                             fluxes_to_minimize,
                             step, m, solver, relax_qssa, qssa_relaxation_strength, parsimony_strength):

        max_idx = [c.index.get_loc(name.split(":")[0]) for name in fluxes_to_maximize]
        min_idx = [c.index.get_loc(name.split(":")[0]) for name in fluxes_to_minimize]
        # run parallel optimization
        Logger.progress("Open parallel pool for each flux.")
        pool = multiprocessing.Pool()
        params = []
        for i in range(0, m):
            params.append(dict(
                i=i,
                c=c,
                A_eq=A_eq,
                b_eq=b_eq,
                bounds=bounds,
                c_out=c_out,
                x0=x0,
                indexes_of_fluxes_to_minimize=min_idx,
                indexes_of_fluxes_to_maximize=max_idx,
                step=step,
                m=m,
                solver=solver,
                relax_qssa=relax_qssa,
                qssa_relaxation_strength=qssa_relaxation_strength,
                parsimony_strength=parsimony_strength
            ))
        result = pool.map(_do_parallel_loop, params)
        # gather results
        xmin = np.zeros(x0.shape)
        xmax = np.zeros(x0.shape)
        for i in range(0, m):
            xmin[i] = result[i][0]
            xmax[i] = result[i][1]
        return xmin, xmax

    @staticmethod
    # def __solve_with_cvxpy_using_warm_solver(warm_solver,
    #                                          c, A_eq, b_eq, bounds, x0,
    #                                          fluxes_to_maximize,
    #                                          fluxes_to_minimize,
    #                                          step, m, solver, relax_qssa):
    def __solve_with_cvxpy_using_warm_solver(warm_solver,
                                             c, x0,
                                             fluxes_to_maximize,
                                             fluxes_to_minimize,
                                             step, m):
        max_idx = [c.index.get_loc(name.split(":")[0]) for name in fluxes_to_maximize]
        min_idx = [c.index.get_loc(name.split(":")[0]) for name in fluxes_to_minimize]
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
        for i in range(0, m):
            if (i % step) == 0:
                Logger.progress(f" flux {i+1}/{m} ...")
                # self.progress_bar.set_value(i, message=f" flux {i+1}/{m} ...")
            cf = DataFrame(data=np.zeros(c.shape), index=c.index)
            if (i in max_idx) or (i in min_idx):
                xmin[i] = x0[i]
                xmax[i] = x0[i]
            else:
                # min
                cf.iloc[i, 0] = 1.0
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
                cf.iloc[i, 0] = -1.0
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
