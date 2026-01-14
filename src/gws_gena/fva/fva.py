import multiprocessing
from copy import deepcopy

import cvxpy as cp
import numpy as np
from gws_core import (
    BadRequestException,
    ConfigParams,
    ConfigSpecs,
    FloatParam,
    InputSpec,
    InputSpecs,
    Logger,
    OutputSpec,
    OutputSpecs,
    StrParam,
    Table,
    TableConcatHelper,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingStyle,
    task_decorator,
)

# from joblib import Parallel, delayed
from pandas import DataFrame

from ..fba.fba import FBA
from ..fba.fba_helper.fba_helper import FBAHelper
from ..fba.fba_result import FBAOptimizeResult
from ..network.network import Network
from ..twin.flat_twin import FlatTwin
from ..twin.helper.twin_annotator_helper import TwinAnnotatorHelper
from ..twin.helper.twin_helper import TwinHelper
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
    gamma = kwargs["gamma"]

    if (i % step) == 0:
        Logger.progress(f" flux {i + 1}/{m} ...")
        # self.progress_bar.set_value(i, message=f" flux {i+1}/{m} ...")

    cf = DataFrame(data=np.zeros(c.shape), index=c.index)
    if (i in indexes_of_fluxes_to_minimize) or (i in indexes_of_fluxes_to_maximize):
        xmin = x0[i]
        xmax = x0[i]
    else:
        bounds = deepcopy(bounds)
        for k in indexes_of_fluxes_to_minimize:
            bounds[k][1] = x0[k] * gamma

        for k in indexes_of_fluxes_to_maximize:
            bounds[k][0] = x0[k] * gamma

        # min
        cf.iloc[i, 0] = 1.0
        if solver == "quad":
            res_fva, _ = FBAHelper.solve_cvxpy(
                cf,
                A_eq,
                b_eq,
                bounds,
                c_out,
                relax_qssa=relax_qssa,
                qssa_relaxation_strength=qssa_relaxation_strength,
                parsimony_strength=parsimony_strength,
                verbose=False,
            )
        else:
            res_fva: FBAOptimizeResult = FBAHelper.solve_scipy(
                cf, A_eq, b_eq, bounds, c_out, solver=solver
            )
        xmin = res_fva.x[i] if res_fva.x is not None else 0.0

        # max
        cf.iloc[i, 0] = -1.0
        if solver == "quad":
            res_fva, _ = FBAHelper.solve_cvxpy(
                cf,
                A_eq,
                b_eq,
                bounds,
                c_out,
                relax_qssa=relax_qssa,
                qssa_relaxation_strength=qssa_relaxation_strength,
                parsimony_strength=parsimony_strength,
                verbose=False,
            )
        else:
            res_fva: FBAOptimizeResult = FBAHelper.solve_scipy(
                cf, A_eq, b_eq, bounds, c_out, solver=solver
            )
        xmax = res_fva.x[i] if res_fva.x is not None else 0.0
    return xmin, xmax


@task_decorator(
    "FVA",
    human_name="FVA",
    short_description="Flux variability analysis",
    style=TypingStyle.material_icon(
        material_icon_name="settings_suggest", background_color="#d9d9d9"
    ),
)
class FVA(Task):
    """
    FVA class

    Performs Flux Variability Analysis (FVA).
    It calculates the minimum and maximum flux values for each reaction in a metabolic network while satisfying certain constraints;

    It is based on the paper of (Gudmundsson and Thiele, Bioinformatics 2010).
    See also:
    > Steinn Gudmundsson & Ines Thiele, Computationally efficient flux variability analysis,
    BMC Bioinformatics, volume 11, Article number: 489 (2010),
    https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-11-489
    """

    input_specs = InputSpecs(
        {
            "twin": InputSpec(
                Twin, human_name="Digital twin", short_description="The digital twin to analyze"
            )
        }
    )
    output_specs = OutputSpecs(
        {
            "twin": OutputSpec(
                Twin,
                human_name="Simulated digital twin",
                short_description="The simulated digital twin",
            ),
            "fva_result": OutputSpec(
                FVAResult, human_name="FVA result table", short_description="The FVA result tables"
            ),
        }
    )
    config_specs = ConfigSpecs(
        {
            "gamma": FloatParam(
                default_value=1.0,
                human_name="γ",
                min_value=0.0,
                max_value=1.0,
                visibility=StrParam.PROTECTED_VISIBILITY,
                short_description="γ determines whether the analysis is conducted with respect to suboptimal network states (where 0 ≤ γ < 1) or to the optimal state (where γ = 1). A value of 0.9 implies that the objective must be at least 90% of its maximum.",
            )
        }
    ).merge_specs(FBA.config_specs)
    __CVXPY_MAX_ITER = 100000

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        self.log_info_message(message="Creating problem ...")
        twin = inputs["twin"]
        solver = params["solver"]
        relax_qssa = params["relax_qssa"]

        if relax_qssa and solver != "quad":
            self.log_info_message(message=f"Change solver to '{solver}' for constrain relaxation.")
            solver = "quad"

        # retrieve the context of the twin
        context = next(iter(twin.contexts.values()))

        number_of_simulations = params["number_of_simulations"]
        # If number_of_simulations is not provided, keep all the simulations
        if number_of_simulations is None:
            number_reaction_simulation = next(
                (len(measure.target) for _, measure in context.reaction_data.items()), 1
            )
            number_metabolite_simulation = next(
                (len(measure.target) for _, measure in context.compound_data.items()), 1
            )
            number_of_simulations = min(number_reaction_simulation, number_metabolite_simulation)

        # check the length of the values
        for name_measure, measure in context.reaction_data.items():
            if len(measure.target) < number_of_simulations:
                raise Exception(
                    "The number of target values must be at least equal to the number of simulations. For "
                    + name_measure
                    + ", there are "
                    + str(len(measure.target))
                    + " values of targets while the number of simulations is set to "
                    + str(number_of_simulations)
                )
            if len(measure.upper_bound) < number_of_simulations:
                raise Exception(
                    "The number of upper bound values must be at least equal to the number of simulations. For "
                    + name_measure
                    + ", there are "
                    + str(len(measure.upper_bound))
                    + " values of upper bound while the number of simulations is set to "
                    + str(number_of_simulations)
                )
            if len(measure.lower_bound) < number_of_simulations:
                raise Exception(
                    "The number of lower bound values must be at least equal to the number of simulations. For "
                    + name_measure
                    + ", there are "
                    + str(len(measure.lower_bound))
                    + " values of lower_bound while the number of simulations is set to "
                    + str(number_of_simulations)
                )
            if len(measure.confidence_score) < number_of_simulations:
                raise Exception(
                    "The number of confidence score values must be at least equal to the number of simulations. For "
                    + name_measure
                    + ", there are "
                    + str(len(measure.confidence_score))
                    + " values of confidence score while the number of simulations is set to "
                    + str(number_of_simulations)
                )
        for name_measure, measure in context.compound_data.items():
            if len(measure.target) < number_of_simulations:
                raise Exception(
                    "The number of target values must be at least equal to the number of simulations. For "
                    + name_measure
                    + ", there are "
                    + str(len(measure.target))
                    + " values of targets while the number of simulations is set to "
                    + str(number_of_simulations)
                )
            if len(measure.upper_bound) < number_of_simulations:
                raise Exception(
                    "The number of upper bound values must be at least equal to the number of simulations. For "
                    + name_measure
                    + ", there are "
                    + str(len(measure.upper_bound))
                    + " values of upper bound while the number of simulations is set to "
                    + str(number_of_simulations)
                )
            if len(measure.lower_bound) < number_of_simulations:
                raise Exception(
                    "The number of lower bound values must be at least equal to the number of simulations. For "
                    + name_measure
                    + ", there are "
                    + str(len(measure.lower_bound))
                    + " values of lower_bound while the number of simulations is set to "
                    + str(number_of_simulations)
                )
            if len(measure.confidence_score) < number_of_simulations:
                raise Exception(
                    "The number of confidence score values must be at least equal to the number of simulations. For "
                    + name_measure
                    + ", there are "
                    + str(len(measure.confidence_score))
                    + " values of confidence score while the number of simulations is set to "
                    + str(number_of_simulations)
                )

        fva_results: list[FVAResult] = []
        twin_helper = TwinHelper()

        # If number of simulations is not None, there is a context with simulations
        if number_of_simulations:
            # run through the number of simulations
            for i in range(0, number_of_simulations):
                new_twin = twin_helper.build_twin_from_sub_context(twin, i)
                fva_results.append(self.call_fva((i, new_twin, params)))
                self.update_progress_value(
                    ((i + 1) / number_of_simulations) * 100,
                    message="Running FVA for all simulations",
                )
        else:  # if number of simulations is None, there is no context provided, so we run only one FVA
            new_twin = twin_helper.build_twin_from_sub_context(twin, 0)
            fva_results.append(self.call_fva((0, new_twin, params)))
            self.update_progress_value(100, message="Running FVA")

        # annotate twin
        self.log_info_message("Annotating the twin")
        annotator_helper = TwinAnnotatorHelper()
        annotator_helper.attach_message_dispatcher(self.message_dispatcher)
        result_twin = annotator_helper.annotate_from_fva_results(twin, fva_results)

        self.log_info_message("Merging all fba results")
        # merge all fba results
        self.log_info_message("Creating lists")
        flux_tables: list[Table] = []
        sv_tables: list[Table] = []
        if len(fva_results) > 1:
            # If there are multiple simulations, add suffix to the index
            # like this "simu0", "simu1"...
            for i, fva_result in enumerate(fva_results):
                flux_table = fva_result.get_flux_table()
                sv_table = fva_result.get_sv_table()

                # Add simulation suffix to index, starting from _0
                flux_data = flux_table.get_data()
                sv_data = sv_table.get_data()

                # Add suffix to index names
                flux_data.index = [f"{idx}_simu{i}" for idx in flux_data.index]
                sv_data.index = [f"{idx}_simu{i}" for idx in sv_data.index]

                # Create new tables with modified indices
                flux_table_modified = Table(flux_data)
                sv_table_modified = Table(sv_data)

                flux_tables.append(flux_table_modified)
                sv_tables.append(sv_table_modified)
        else:
            flux_tables.append(fva_results[0].get_flux_table())
            sv_tables.append(fva_results[0].get_sv_table())
        self.log_info_message("Concat flux table")
        merged_flux_table: Table = TableConcatHelper.concat_table_rows(flux_tables)
        self.log_info_message("Concat sv table")
        merged_sv_table: Table = TableConcatHelper.concat_table_rows(sv_tables)
        self.log_info_message("Create FVAResult")
        merged_fva_result = FVAResult(merged_flux_table.get_data(), merged_sv_table.get_data())

        return {"fva_result": merged_fva_result, "twin": result_twin}

    @staticmethod
    def __solve_with_parloop(
        c,
        A_eq,
        b_eq,
        bounds,
        c_out,
        x0,
        fluxes_to_maximize,
        fluxes_to_minimize,
        step,
        m,
        solver,
        relax_qssa,
        qssa_relaxation_strength,
        parsimony_strength,
        gamma,
    ):
        max_idx = [c.index.get_loc(name.split(":")[0]) for name in fluxes_to_maximize]
        min_idx = [c.index.get_loc(name.split(":")[0]) for name in fluxes_to_minimize]
        # run parallel optimization
        Logger.progress("Open parallel pool for each flux.")
        pool = multiprocessing.Pool()
        params = []
        for i in range(0, m):
            params.append(
                {
                    "i": i,
                    "c": c,
                    "A_eq": A_eq,
                    "b_eq": b_eq,
                    "bounds": bounds,
                    "c_out": c_out,
                    "x0": x0,
                    "indexes_of_fluxes_to_minimize": min_idx,
                    "indexes_of_fluxes_to_maximize": max_idx,
                    "step": step,
                    "m": m,
                    "solver": solver,
                    "relax_qssa": relax_qssa,
                    "qssa_relaxation_strength": qssa_relaxation_strength,
                    "parsimony_strength": parsimony_strength,
                    "gamma": gamma,
                }
            )
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
    def __solve_with_cvxpy_using_warm_solver(
        warm_solver, c, x0, fluxes_to_maximize, fluxes_to_minimize, step, m, gamma
    ):
        max_idx = [c.index.get_loc(name.split(":")[0]) for name in fluxes_to_maximize]
        min_idx = [c.index.get_loc(name.split(":")[0]) for name in fluxes_to_minimize]
        lb = warm_solver["lb_par"]
        ub = warm_solver["ub_par"]
        for k in max_idx:
            lb.value[k] = x0[k] * gamma

        for k in min_idx:
            ub.value[k] = x0[k] * gamma

        xmin = np.zeros(x0.shape)
        xmax = np.zeros(x0.shape)
        x = warm_solver["x"]
        c_par = warm_solver["c_par"]
        prob = warm_solver["prob"]
        for i in range(0, m):
            if (i % step) == 0:
                Logger.progress(f" flux {i + 1}/{m} ...")
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
                except Exception:
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
                except Exception:
                    Logger.progress("OSQP failed. Switch to ECOS solver")
                    prob.solve(solver=cp.ECOS, max_iters=FVA.__CVXPY_MAX_ITER, verbose=False)
                xmax[i] = x.value[i]
        return xmin, xmax

    def call_fva(self, data: tuple[int, Twin, ConfigParams]) -> FVAResult:
        j, twin, params = data
        solver = params["solver"]
        gamma = params["gamma"]
        parsimony_strength = 0  # params["parsimony_strength"]
        qssa_relaxation_strength = params["qssa_relaxation_strength"]
        relax_qssa = params["relax_qssa"]

        if isinstance(twin, FlatTwin):
            flat_twin = twin
        else:
            flat_twin: FlatTwin = twin.flatten()

        c, A_eq, b_eq, bounds, c_out, fluxes_to_maximize, fluxes_to_minimize = (
            FBAHelper.build_problem(
                flat_twin,
                biomass_optimization=params["biomass_optimization"],
                fluxes_to_maximize=params["fluxes_to_maximize"],
                fluxes_to_minimize=params["fluxes_to_minimize"],
            )
        )

        self.log_info_message(message=f"Starting optimization with solver '{solver}' ...")
        if solver == "quad":
            res, warm_solver = FBAHelper.solve_cvxpy(
                c,
                A_eq,
                b_eq,
                bounds,
                c_out,
                relax_qssa=relax_qssa,
                qssa_relaxation_strength=qssa_relaxation_strength,
                parsimony_strength=parsimony_strength,
                verbose=False,
            )
        else:
            res: FBAOptimizeResult = FBAHelper.solve_scipy(
                c, A_eq, b_eq, bounds, c_out, solver=solver
            )
        self.log_info_message(
            message=res.message if res and res.message else "No message from solver."
        )
        if not res.success:
            raise BadRequestException(f"Convergence error. Optimization message: '{res.message}'")

        self.log_info_message(
            message=f"Performing variability analysis around the optimal value using solver '{solver}' ..."
        )
        x0 = res.x
        m = x0.shape[0] if x0 is not None else 0
        step = max(1, int(m / 10))  # plot only 10 iterations on screen

        flat_net: Network = flat_twin.get_flat_network()
        fluxes_to_minimize = FBAHelper._expand_fluxes_by_names(fluxes_to_minimize, flat_net)
        fluxes_to_maximize = FBAHelper._expand_fluxes_by_names(fluxes_to_maximize, flat_net)

        if solver == "quad":
            xmin, xmax = self.__solve_with_cvxpy_using_warm_solver(
                warm_solver, c, x0, fluxes_to_maximize, fluxes_to_minimize, step, m, gamma
            )
        else:
            xmin, xmax = self.__solve_with_parloop(
                c,
                A_eq,
                b_eq,
                bounds,
                c_out,
                x0,
                fluxes_to_maximize,
                fluxes_to_minimize,
                step,
                m,
                solver,
                relax_qssa,
                qssa_relaxation_strength,
                parsimony_strength,
                gamma,
            )
        res.xmin = xmin
        res.xmax = xmax
        fva_result = FVAResult()
        fva_result = fva_result.from_optimized_result(res)
        fva_result = FVAResult(fva_result.get_fluxes_dataframe(), fva_result.get_sv_dataframe())

        return fva_result
