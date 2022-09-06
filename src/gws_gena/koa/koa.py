# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas
from gws_core import (BadRequestException, BoolParam, ConfigParams, InputSpec,
                      ListParam, Logger, OutputSpec, StrParam, Task,
                      TaskInputs, TaskOutputs, task_decorator)
from pandas import DataFrame

from ..data.ec_table import ECTable
from ..data.entity_id_table import EntityIDTable
from ..fba.fba import FBA
from ..fba.fba_helper.fba_helper import FBAHelper
from ..fba.fba_result import FBAResult
from ..network.reaction.helper.reaction_knockout_helper import \
    ReactionKnockOutHelper
from ..twin.flat_twin import FlatTwin
from ..twin.helper.twin_annotator_helper import TwinAnnotatorHelper
from ..twin.twin import Twin
from .koa_result import KOAResult


@task_decorator("KOA", human_name="KOA", short_description="Knockout Analysis")
class KOA(Task):
    """
    KOA class.
    """

    input_specs = {
        'twin': InputSpec(Twin, human_name="Digital twin", short_description="The digital twin to analyze"),
        'ko_table': InputSpec([EntityIDTable, ECTable], human_name="KO table", short_description="The table of KO hypotheses"),
    }
    output_specs = {
        'twin': OutputSpec(Twin, human_name="Simulated digital twin", short_description="The simulated digital twin"),
        'koa_result': OutputSpec(KOAResult, human_name="KOA result tables", short_description="The KOA result tables")
    }
    config_specs = {
        **FBA.config_specs,
        # 'monitored_fluxes':
        # ListParam(
        #     optional=True, human_name="Monitored fluxes", visibility=ListParam.PROTECTED_VISIBILITY,
        #     short_description="The list of fluxes to monitor. By default, all the reactions are monitored. Set 'biomass' to only monitor the biomass reaction flux."),
        'ko_delimiter':
        StrParam(
            default_value=",", human_name="Multiple KO delimiter",
            short_description="The delimiter used to separate IDs or EC numbers when multiple KO are performed")}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        ko_table: ECTable = inputs["ko_table"]
        twin: FlatTwin = inputs["twin"].flatten()
        solver = params["solver"]
        biomass_optimization = params["biomass_optimization"]
        fluxes_to_maximize = params["fluxes_to_maximize"]
        fluxes_to_minimize = params["fluxes_to_minimize"]
        fill_gaps_with_sinks = params["fill_gaps_with_sinks"]
        ignore_cofactors = params["ignore_cofactors"]
        relax_qssa = params["relax_qssa"]
        qssa_relaxation_strength = params["qssa_relaxation_strength"]
        # monitored_fluxes = params.get_value("monitored_fluxes", [])
        ko_delimiter = params.get_value("ko_delimiter", ",")

        # is_monitored_fluxes_expanded = False
        # full_ko_result_df = DataFrame()
        full_ko_result_list = []
        for i in range(0, ko_table.nb_rows):
            current_ko_table = ko_table.select_by_row_positions([i])

            ko_info = current_ko_table.get_data().iloc[0, :].values.tolist()
            ko_id: str = current_ko_table.get_ids()[0]

            perc = 100 * (i/ko_table.nb_rows)
            self.update_progress_value(
                perc, message=f"Step {i+1}/{ko_table.nb_rows}: analyzing knockout '{ko_id}' ...")

            current_ko_twin = twin.copy()
            helper = ReactionKnockOutHelper()
            helper.attach_task(self)
            for _, net in current_ko_twin.networks.items():
                _, invalid_ko_ids = helper.knockout_list_of_reactions(
                    net, current_ko_table, ko_delimiter=ko_delimiter, inplace=True)

            fba_helper = FBAHelper()
            fba_helper.attach_task(self)
            current_result: FBAResult = fba_helper.run(
                current_ko_twin, solver, fluxes_to_maximize, fluxes_to_minimize,
                biomass_optimization=biomass_optimization, fill_gaps_with_sinks=fill_gaps_with_sinks,
                ignore_cofactors=ignore_cofactors, relax_qssa=relax_qssa,
                qssa_relaxation_strength=qssa_relaxation_strength)

            # if monitored_fluxes:
            #     if len(monitored_fluxes) == 1 and monitored_fluxes[0].lower() == 'biomass':
            #         current_fluxes = current_result.get_biomass_flux_dataframe()
            #     else:
            #         current_fluxes = current_result.get_fluxes_dataframe()
            #         if not is_monitored_fluxes_expanded:
            #             monitored_fluxes = FBAHelper._expand_fluxes_by_names(
            #                 monitored_fluxes,
            #                 current_ko_twin.get_flat_network()
            #             )
            #         monitored_fluxes_names = [name.split(":")[0] for name in monitored_fluxes]
            #         current_fluxes = current_fluxes.loc[monitored_fluxes_names, :]
            # else:
            #     current_fluxes = current_result.get_fluxes_dataframe()

            current_fluxes = current_result.get_fluxes_dataframe()

            # current_fluxes.columns = ["flux_value", "flux_lower_bound", "flux_upper_bound"]
            # ko_id_df = DataFrame(
            #     data=[ko_info] * current_fluxes.shape[0],
            #     columns=current_ko_table.column_names,
            #     index=current_fluxes.index
            # )

            # flux_name_df = DataFrame(
            #     data=current_fluxes.index.T,
            #     columns=["flux_name"],
            #     index=current_fluxes.index
            # )

            # not_found_df = DataFrame(
            #     data=[", ".join(invalid_ko_ids)] * current_fluxes.shape[0],
            #     columns=["invalid_ko_ids"],
            #     index=current_fluxes.index
            # )

            # current_ko_result_df = pandas.concat(
            #     [ko_id_df, flux_name_df, current_fluxes, not_found_df],
            #     axis=1
            # )

            # full_ko_result_df = pandas.concat(
            #     [full_ko_result_df, current_ko_result_df],
            #     axis=0,
            # )
            # full_ko_result_df.index = range(0, full_ko_result_df.shape[0])

            full_ko_result_list.append({
                "fluxes": current_fluxes,
                "invalid_ko_ids": invalid_ko_ids
            })

        # full_ko_result_df.rename(
        #     columns={ko_table.id_column: "ko_id"},
        #     inplace=True)  # rename the `id_column` to `ko_id`

        koa_result = KOAResult(data=full_ko_result_list,
                               twin=inputs["twin"], ko_table=ko_table)

        # set simulations
        simulations = []
        for i in range(0, ko_table.nb_rows):
            current_ko_table = ko_table.select_by_row_positions([i])

            ko_info = current_ko_table.get_data().iloc[0, :].values.tolist()
            ko_id: str = current_ko_table.get_ids()[0]

            simulations.append({
                "id": f"{ko_id}",
                "name": f"KO analysis: {ko_info}",
                "description": f"Simulation after knockout of reaction(s): {ko_info}"
            })
        koa_result.set_simulations(simulations)

        # annotate twin
        koa_result.set_simulations(simulations)
        helper = TwinAnnotatorHelper()
        helper.attach_task(self)
        twin = helper.annotate_from_koa_result(inputs["twin"], koa_result)

        return {
            "koa_result": koa_result,
            "twin": twin
        }
