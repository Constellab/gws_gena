# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas
from gws_core import (BadRequestException, BoolParam, ConfigParams, ListParam,
                      Logger, StrParam, Task, TaskInputs, TaskOutputs,
                      task_decorator)
from pandas import DataFrame

from ..data.ec_table import ECTable
from ..data.id_table import IDTable
from ..fba.fba import FBA
from ..fba.fba_helper.fba_helper import FBAHelper
from ..fba.fba_result import FBAResult
from ..network.network_helper.reaction_knockout_helper import \
    ReactionKnockOutHelper
from ..twin.twin import FlatTwin, Twin
from .knockout_analysis_result_table import KnockOutAnalysisResultTable


@task_decorator("KnockOutAnalysis")
class KnockOutAnalysis(Task):
    """
    KnockOutAnalysis class.
    """

    input_specs = {
        'twin': (Twin,),
        'ko_table': (IDTable, ECTable,),
    }
    output_specs = {'ko_analysis_result': (KnockOutAnalysisResultTable,)}
    config_specs = {
        **FBA.config_specs,
        'monitored_fluxes': ListParam(optional=True, short_description="The list fluxes to monitor")
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        ko_table: ECTable = inputs["ko_table"]
        twin: FlatTwin = inputs["twin"].flatten()
        solver = params["solver"]
        fluxes_to_maximize = params["fluxes_to_maximize"]
        fluxes_to_minimize = params["fluxes_to_minimize"]
        fill_gaps_with_sinks = params["fill_gaps_with_sinks"]
        ignore_cofactors = params["ignore_cofactors"]
        relax_qssa = params["relax_qssa"]
        monitored_fluxes = params.get("monitored_fluxes", [])

        full_ko_result_df = DataFrame()
        for i in range(0, ko_table.nb_rows):
            current_ko_table = ko_table.select_by_row_indexes([i])
            ko_name: str = current_ko_table.get_ids()[0]

            perc = 100 * (i/ko_table.nb_rows)
            self.update_progress_value(
                perc, message=f"Step {i+1}/{ko_table.nb_rows}: analyzing knockout '{ko_name}' ...")

            current_ko_twin = twin.copy()
            for _, net in current_ko_twin.networks.items():
                ReactionKnockOutHelper.knockout_list_of_reactions(net, current_ko_table, inplace=True)

            current_result: FBAResult = FBAHelper.run(
                current_ko_twin, solver, fluxes_to_maximize, fluxes_to_minimize,
                fill_gaps_with_sinks=fill_gaps_with_sinks, ignore_cofactors=ignore_cofactors, relax_qssa=relax_qssa)

            current_fluxes = current_result.get_fluxes_as_table()
            if len(monitored_fluxes):
                current_fluxes = current_fluxes.loc[monitored_fluxes, :]
            current_fluxes.columns = ["flux_value", "flux_lower_bound", "flux_upper_bound"]

            ko_name_df = DataFrame(
                data=[[ko_name]] * current_fluxes.shape[0],
                columns=["ko"],
                index=current_fluxes.index
            )

            flux_name_df = DataFrame(
                data=current_fluxes.index.T,
                columns=["flux_name"],
                index=current_fluxes.index
            )

            current_ko_result_df = pandas.concat(
                [ko_name_df, flux_name_df, current_fluxes],
                axis=1
            )

            full_ko_result_df = pandas.concat(
                [full_ko_result_df, current_ko_result_df],
                axis=0,
            )
            full_ko_result_df.index = range(0, full_ko_result_df.shape[0])

        ko_analysis_result = KnockOutAnalysisResultTable(data=full_ko_result_df)
        return {"ko_analysis_result": ko_analysis_result}
