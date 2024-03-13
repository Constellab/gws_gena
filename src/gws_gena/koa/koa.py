# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, StrParam, Task, TaskInputs, TaskOutputs,
                      task_decorator, TypingStyle)

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


@task_decorator("KOA", human_name="KOA", short_description="Knockout Analysis",
style=TypingStyle.material_icon(material_icon_name="delete_forever", background_color="#d9d9d9"))
class KOA(Task):
    """
    Knock-out analysis class.

    Perform an FBA by knocking out some reactions.
    Reactions to knockout can be provided with a EntityIDTable or a ECTable.
    Please note that if you provide a EntityIDTable, the reaction id must be "network_reaction1".

    If you want to perform multiple knockout at the same time; provide them like this:
    id
    "reaction1, reaction2, reaction3"
    """

    input_specs = InputSpecs({
        'twin': InputSpec(Twin, human_name="Digital twin", short_description="The digital twin to analyze"),
        'ko_table': InputSpec([EntityIDTable, ECTable], human_name="KO table", short_description="The table of KO hypotheses"),
    })
    output_specs = OutputSpecs({
        'twin': OutputSpec(Twin, human_name="Simulated digital twin", short_description="The simulated digital twin"),
        'koa_result': OutputSpec(KOAResult, human_name="KOA result tables", short_description="The KOA result tables")
    })
    config_specs = {
        **FBA.config_specs,
        'ko_delimiter':
        StrParam(
            default_value=",", human_name="Multiple KO delimiter",
            short_description="The delimiter used to separate IDs or EC numbers when multiple KO are performed")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        ko_table: ECTable = inputs["ko_table"]
        twin: FlatTwin = inputs["twin"].flatten()
        solver = params["solver"]
        biomass_optimization = params["biomass_optimization"]
        fluxes_to_maximize = params["fluxes_to_maximize"]
        fluxes_to_minimize = params["fluxes_to_minimize"]
        relax_qssa = params["relax_qssa"]
        qssa_relaxation_strength = params["qssa_relaxation_strength"]
        parsimony_strength = params["parsimony_strength"]
        ko_delimiter = params.get_value("ko_delimiter", ",")

        # is_monitored_fluxes_expanded = False
        full_ko_result_list = []
        for i in range(0, ko_table.nb_rows):
            current_ko_table = ko_table.select_by_row_indexes([i])

            ko_info = current_ko_table.get_data().iloc[0, :].values.tolist()
            if isinstance(current_ko_table, EntityIDTable):
                ko_id: str = current_ko_table.get_ids()[0]
            else:
                ko_id: str =  current_ko_table.get_ec_numbers()[0]

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
                biomass_optimization=biomass_optimization,
                relax_qssa=relax_qssa,
                qssa_relaxation_strength=qssa_relaxation_strength,
                parsimony_strength=parsimony_strength)

            current_fluxes = current_result.get_fluxes_dataframe()

            full_ko_result_list.append({
                "fluxes": current_fluxes,
                "invalid_ko_ids": invalid_ko_ids
            })

        koa_result = KOAResult(data=full_ko_result_list,
                               twin=inputs["twin"], ko_table=ko_table)

        # set simulations
        simulations = []
        for i in range(0, ko_table.nb_rows):
            current_ko_table = ko_table.select_by_row_indexes([i])

            ko_info = current_ko_table.get_data().iloc[0, :].values.tolist()

            if isinstance(current_ko_table, EntityIDTable):
                ko_id: str = current_ko_table.get_ids()[0]
            else:
                ko_id: str =  current_ko_table.get_ec_numbers()[0]

            simulations.append({
                "id": f"{ko_id}",
                "name": f"KO analysis: {ko_info}",
                "description": f"Simulation after knockout of reaction(s): {ko_info}"
            })

        # annotate twin
        koa_result.set_simulations(simulations)
        helper = TwinAnnotatorHelper()
        helper.attach_task(self)
        twin = helper.annotate_from_koa_result(inputs["twin"], koa_result)

        return {
            "koa_result": koa_result,
            "twin": twin
        }
