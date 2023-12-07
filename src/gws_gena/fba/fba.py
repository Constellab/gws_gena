# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import multiprocessing
from typing import Tuple
from gws_core import (BoolParam, ConfigParams, FloatParam, InputSpec, Logger,
                      InputSpecs, ListParam, OutputSpec, OutputSpecs, StrParam, TableConcatHelper,
                      Task, TaskInputs, TaskOutputs, task_decorator, Table, IntParam)

from ..twin.helper.twin_annotator_helper import TwinAnnotatorHelper
from ..twin.twin import Twin
from .fba_helper.fba_helper import FBAHelper
from .fba_result import FBAResult

from ..context.variable import Variable
from ..context.context import Context
from ..context.measure import Measure
from ..context.typing.measure_typing import MeasureDict
from ..context.typing.variable_typing import VariableDict
from ..twin.twin_builder import TwinBuilder

from gws_gena.network.network import Network


@task_decorator("FBA", human_name="FBA", short_description="Flux balance analysis")
class FBA(Task):
    """
    FBA task class

    Performs Flux Balance Analysis from a digital twin.

    A digital twin is a mathematical representation of the metabolic interactions involved in a living cell or microbial organism
    (e.g. animal cell, bacteria, fungus, etc.).
    """

    input_specs = InputSpecs({'twin': InputSpec(Twin, human_name="Digital twin",
                             short_description="The digital twin to analyze")})
    output_specs = OutputSpecs({
        'twin': OutputSpec(Twin, human_name="Simulated digital twin", short_description="The simulated digital twin"),
        'fba_result': OutputSpec(FBAResult, human_name="FBA result tables", short_description="The FBA result tables")
    })
    config_specs = {
        "biomass_optimization":
        StrParam(
            allowed_values=["", "maximize", "minimize"],
            default_value=None, optional=True, human_name="Biomass optimization",
            short_description="Biomass optimization"),
        "fluxes_to_maximize":
        ListParam(
            default_value=None, optional=True, visibility=StrParam.PROTECTED_VISIBILITY,
            human_name="Fluxes to maximize", short_description="The fluxes to maximize"),
        "fluxes_to_minimize":
        ListParam(
            default_value=None, optional=True, visibility=StrParam.PROTECTED_VISIBILITY,
            human_name="Fluxes to minimize", short_description="The fluxes to minimize"),
        "solver":
        StrParam(
            default_value="quad", visibility=StrParam.PROTECTED_VISIBILITY,
            allowed_values=["quad", "highs-ds", "highs-ipm", "highs", "interior-point"],
            human_name="Solver", short_description="The optimization solver. It is recommended to use `quad`. Other solvers are in `beta` versions."),
        "relax_qssa":
        BoolParam(
            default_value=False, visibility=StrParam.PROTECTED_VISIBILITY, human_name="Relax QSSA",
            short_description="True to relaxing the quasi-steady state assumption (QSSA) constrain (`quad` solver is used). False otherwise."),
        "qssa_relaxation_strength":
        FloatParam(
            default_value=0.0, min_value=0.0, visibility=StrParam.PROTECTED_VISIBILITY,
            human_name="QSSA relaxation strength",
            short_description="Used only if the QSSA is relaxed. The higher is the strength, the stronger is the QSSA. Hint: Set to the number of reactions to have strong QSSA contrain."),
        "parsimony_strength":
        FloatParam(
            default_value=0.0, min_value=0.0, visibility=StrParam.PROTECTED_VISIBILITY,
            human_name="Parsimony strength",
            short_description="Set True to perform parsimonious FBA (pFBA). In this case the quad solver is used. Set False otherwise"),
        "number_of_simulations":
        IntParam(
            default_value=1, min_value=1, visibility=StrParam.PROTECTED_VISIBILITY,
            human_name="Number of simulations",
            short_description="Set the number of simulations to perform. You must provide at least the same number of measures in the context.")
        #,
        #"number_of_processes":
        #IntParam(
        #    default_value=2, min_value=1, visibility=StrParam.PROTECTED_VISIBILITY,
        #    human_name="Number of processes",
        #    short_description="Set the number of processes to use to parallelise the execution of FBA.")
        }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        twin = inputs["twin"]
        number_of_simulations = params["number_of_simulations"]

        # retrieve the context of the twin
        context = next(iter(twin.contexts.values()))
        # retrieve the network of the twin
        network = next(iter(twin.networks.values()))

        # check the length of the values
        for name_measure, measure in context.measures.items():
            if (len(measure.target) < number_of_simulations):
                raise Exception(
                    "The number of target values must be at least equal to the number of simulations. For " +
                    name_measure + ", there are " + str(len(measure.target)) +
                    " values of targets while the number of simulations is set to " + str(number_of_simulations))
            if (len(measure.upper_bound) < number_of_simulations):
                raise Exception(
                    "The number of upper bound values must be at least equal to the number of simulations. For " +
                    name_measure + ", there are " + str(len(measure.upper_bound)) +
                    " values of upper bound while the number of simulations is set to " +
                    str(number_of_simulations))
            if (len(measure.lower_bound) < number_of_simulations):
                raise Exception(
                    "The number of lower bound values must be at least equal to the number of simulations. For " +
                    name_measure + ", there are " + str(len(measure.lower_bound)) +
                    " values of lower_bound while the number of simulations is set to " +
                    str(number_of_simulations))
            if (len(measure.confidence_score) < number_of_simulations):
                raise Exception(
                    "The number of confidence score values must be at least equal to the number of simulations. For " +
                    name_measure + ", there are " + str(len(measure.confidence_score)) +
                    " values of confidence score while the number of simulations is set to " +
                    str(number_of_simulations))

        fba_results: List[FBAResult] = []

        # indexed_data_list = []
        # for i in range(0, number_of_simulations):  # run through the number of simulations
        #     new_twin = self.build_twin(twin, i)
        #     indexed_data_list.append((i, new_twin, params))

        # i = 0
        # try:
        #     with multiprocessing.Pool(processes=params["number_of_processes"]) as pool:
        #         # chunksize to 1 because each FBA takes time so we can assign a sub process to only 1 FBA
        #         for result in pool.imap_unordered(self.call_fba, indexed_data_list, chunksize=1):

        #             if result is not None:
        #                 fba_results.append(result)
        #                 self.update_progress_value((i + 1) / number_of_simulations * 100,
        #                                            'Running FBA for all simulations')
        #                 i += 1
        # except Exception as e:
        #     Logger.log_exception_stack_trace(e)
        #     raise e

        for i in range(0, number_of_simulations):  # run through the number of simulations
            new_twin = self.build_twin(twin, i)
            fba_results.append(self.call_fba((i, new_twin, params)))
            self.update_progress_value(((i+1) / number_of_simulations) * 100, message="Running FBA for all simulations")

        self.log_info_message('Annotating the twin')
        annotator_helper = TwinAnnotatorHelper()
        annotator_helper.attach_task(self)
        result_twin = annotator_helper.annotate_from_fba_results(twin, fba_results)
        self.log_info_message('Merging all fba results')
        # merge all fba results
        self.log_info_message('Creating lists')
        flux_tables: List[Table] = []
        sv_tables: List[Table] = []
        for fba_result in fba_results:
            flux_tables.append(fba_result.get_flux_table())
            sv_tables.append(fba_result.get_sv_table())
        self.log_info_message('Concat flux table')
        merged_flux_table: Table = TableConcatHelper.concat_table_rows(flux_tables)
        self.log_info_message('Concat sv table')
        merged_sv_table: Table = TableConcatHelper.concat_table_rows(sv_tables)
        self.log_info_message('Create FBAResult')
        merged_fba_result = FBAResult(merged_flux_table.get_data(), merged_sv_table.get_data())

        return {
            "fba_result": merged_fba_result,
            "twin": result_twin
        }

    def build_twin(self, base_twin: Twin, index: int) -> Twin:
        new_twin = Twin()

        network = next(iter(base_twin.networks.values()))
        new_twin.add_network(network)

        base_context = next(iter(base_twin.contexts.values()))
        new_context = self.build_context(base_context, index)
        new_twin.add_context(new_context, related_network=network)

        return new_twin

    def build_context(self, base_context: Context, index: int) -> Context:
        ctx = Context()
        for name_measure, measure in base_context.measures.items():  # run through the number of context measures
            value_target = measure.target[index]
            value_upper = measure.upper_bound[index]
            value_lower = measure.lower_bound[index]
            value_confidence_score = measure.confidence_score[index]
            # Create a new measure
            measure = Measure(
                MeasureDict(
                    id=name_measure,
                    target=value_target,
                    upper_bound=value_upper,
                    lower_bound=value_lower,
                    confidence_score=value_confidence_score,
                    variables=[
                        VariableDict(
                            coefficient=1.0,
                            reference_id=name_measure.split('measure_')[-1],
                            reference_type=Variable.REACTION_REFERENCE_TYPE
                        )]
                ))
            ctx.add_measure(measure)

        return ctx

    def call_fba(self, data: Tuple[int, Twin, ConfigParams]) -> FBAResult:
        j, twin, params = data

        # Run the FBA for this twin
        fba_helper = FBAHelper()
        #fba_helper.attach_task(self)
        fba_result = fba_helper.run(
            twin, solver=params["solver"],
            fluxes_to_maximize=params["fluxes_to_maximize"],
            fluxes_to_minimize=params["fluxes_to_minimize"],
            biomass_optimization=params["biomass_optimization"],
            relax_qssa=params["relax_qssa"],
            qssa_relaxation_strength=params["qssa_relaxation_strength"],
            parsimony_strength=params["parsimony_strength"])


        return fba_result
