# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas
from gws_core import (BadRequestException, BoolParam, ConfigParams, InputSpec,
                      ListParam, Logger, OutputSpec, StrParam, Task,
                      TaskInputs, TaskOutputs, task_decorator)
from pandas import DataFrame

from ...data.ec_table import ECTable
from ...data.entity_id_table import EntityIDTable
from ...fba.fba_helper.fba_helper import FBAHelper
from ...fba.fba_result import FBAResult
from ...network.helper.reaction_knockout_helper import ReactionKnockOutHelper
from ...twin.flat_twin import FlatTwin
from ...twin.twin import Twin
from ..v031.dep_koa_result_table import KOAResultTable
from .dep_fba import FBA


@task_decorator("KOA", human_name="KOA", short_description="Depreacted KnockOut Analysis",
                hide=True, deprecated_since='0.3.1', deprecated_message="Use new version of KOA")
class KOA(Task):
    """
    KOA class.
    """

    input_specs = {
        'twin': InputSpec(Twin),
        'ko_table': InputSpec([EntityIDTable, ECTable]),
    }
    output_specs = {'result': OutputSpec(KOAResultTable)}
    config_specs = {
        **FBA.config_specs,
        'monitored_fluxes': ListParam(optional=True, short_description="The list fluxes to monitor"),
        'ko_delimiter':
        StrParam(
            default_value=",",
            short_description="The delimiter used to separate IDs or EC numbers when multiple KO are performed")}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        ko_table: ECTable = inputs["ko_table"]
        twin: FlatTwin = inputs["twin"].flatten()
        solver = params["solver"]
        fluxes_to_maximize = params["fluxes_to_maximize"]
        fluxes_to_minimize = params["fluxes_to_minimize"]
        fill_gaps_with_sinks = params["fill_gaps_with_sinks"]
        ignore_cofactors = params["ignore_cofactors"]
        relax_qssa = params["relax_qssa"]
        monitored_fluxes = params.get_value("monitored_fluxes", [])
        ko_delimiter = params.get_value("ko_delimiter", ",")

        is_monitored_fluxes_expanded = False
        full_ko_result_df = DataFrame()
        for i in range(0, ko_table.nb_rows):
            current_ko_table = ko_table.select_by_row_positions([i])

            ko_info = current_ko_table.get_data().iloc[0, :].values.tolist()
            ko_id: str = current_ko_table.get_ids()[0]

            perc = 100 * (i/ko_table.nb_rows)
            self.update_progress_value(
                perc, message=f"Step {i+1}/{ko_table.nb_rows}: analyzing knockout '{ko_id}' ...")

            current_ko_twin = twin.copy()
            for net in current_ko_twin.networks.values():
                _, not_found_ids = ReactionKnockOutHelper.knockout_list_of_reactions(
                    net, current_ko_table, ko_delimiter=ko_delimiter, current_task=self, inplace=True)

            fba_helper = FBAHelper()
            fba_helper.attach(self)
            current_result: FBAResult = fba_helper.run(
                current_ko_twin, solver, fluxes_to_maximize, fluxes_to_minimize,
                fill_gaps_with_sinks=fill_gaps_with_sinks, ignore_cofactors=ignore_cofactors, relax_qssa=relax_qssa)

            current_fluxes = current_result.get_fluxes_dataframe()
            if monitored_fluxes:
                if not is_monitored_fluxes_expanded:
                    monitored_fluxes = FBAHelper._expand_fluxes_by_names(
                        monitored_fluxes,
                        current_ko_twin.get_flat_network()
                    )
                monitored_fluxes_names = [x.split(":")[0] for x in monitored_fluxes]
                current_fluxes = current_fluxes.loc[monitored_fluxes_names, :]

            current_fluxes.columns = ["flux_value", "flux_lower_bound", "flux_upper_bound"]
            ko_id_df = DataFrame(
                data=[ko_info] * current_fluxes.shape[0],
                columns=current_ko_table.column_names,
                index=current_fluxes.index
            )

            flux_name_df = DataFrame(
                data=current_fluxes.index.T,
                columns=["flux_name"],
                index=current_fluxes.index
            )

            not_found_df = DataFrame(
                data=[", ".join(not_found_ids)] * current_fluxes.shape[0],
                columns=["not_found_ids"],
                index=current_fluxes.index
            )

            current_ko_result_df = pandas.concat(
                [ko_id_df, flux_name_df, current_fluxes, not_found_df],
                axis=1
            )

            full_ko_result_df = pandas.concat(
                [full_ko_result_df, current_ko_result_df],
                axis=0,
            )
            full_ko_result_df.index = range(0, full_ko_result_df.shape[0])

        full_ko_result_df.rename(
            columns={ko_table.id_column: "ko_id"},
            inplace=True)  # rename the `id_column` to `ko_id`
        koa_result = KOAResultTable(data=full_ko_result_df)
        return {"result": koa_result}
