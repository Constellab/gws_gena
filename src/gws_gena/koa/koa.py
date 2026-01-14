import pandas as pd
from gws_core import (
    ConfigParams,
    ConfigSpecs,
    File,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    StrParam,
    Table,
    TableImporter,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingStyle,
    task_decorator,
)

from ..data.task.transformer_ec_number_table import TransformerECNumberTable
from ..data.task.transformer_entity_id_table import TransformerEntityIDTable
from ..fba.fba import FBA
from ..fba.fba_helper.fba_helper import FBAHelper
from ..fba.fba_result import FBAResult
from ..network.reaction.helper.reaction_knockout_helper import ReactionKnockOutHelper
from ..twin.flat_twin import FlatTwin
from ..twin.helper.twin_annotator_helper import TwinAnnotatorHelper
from ..twin.twin import Twin
from .koa_result import KOAResult


@task_decorator(
    "KOA",
    human_name="KOA",
    short_description="Knockout Analysis",
    style=TypingStyle.material_icon(
        material_icon_name="delete_forever", background_color="#d9d9d9"
    ),
)
class KOA(Task):
    """
    Knock-out analysis class.

    Perform an FBA by knocking out some reactions or genes.
    Reactions to knockout can be provided with a Entity ID Table or a EC Table.
    Genes to knockout can be provided with a Entity ID Table.
    Please note that if you provide a Entity ID Table, the reaction id must be "network_reaction1".

    In the output you will get a twin, a KOA result with the estimated fluxes for each knockout and a summary table.
    This table is useful if you provide genes to know which reactions have been knocked out by which genes.

    If you want to perform multiple knockout at the same time (e.g. id1, id2 and id3); provide them like this:
    id
    "network_id1,network_id2,network_id3"
    "network_id4"
    """

    input_specs = InputSpecs(
        {
            "twin": InputSpec(
                Twin, human_name="Digital twin", short_description="The digital twin to analyze"
            ),
            "ko_table": InputSpec(
                (Table, File), human_name="KO table", short_description="The table of KO hypotheses"
            ),
        }
    )
    output_specs = OutputSpecs(
        {
            "twin": OutputSpec(
                Twin,
                human_name="Simulated digital twin",
                short_description="The simulated digital twin",
            ),
            "koa_result": OutputSpec(
                KOAResult, human_name="KOA result tables", short_description="The KOA result tables"
            ),
            "table_summary": OutputSpec(
                Table,
                human_name="Table Summary",
                short_description="The table summarising the reactions knocked out",
            ),
        }
    )
    config_specs = ConfigSpecs(
        {
            "ko_delimiter": StrParam(
                default_value=",",
                human_name="Multiple KO delimiter",
                short_description="The delimiter used to separate IDs or EC numbers when multiple KO are performed",
            ),
            "type_ko": StrParam(
                allowed_values=["reactions", "genes"],
                default_value="reactions",
                human_name="Type of elements to knock-out",
                short_description="The type of elements provided to knock-out: reactions or genes",
            ),
        }
    ).merge_specs(FBA.config_specs)

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        ko_table_input = inputs["ko_table"]
        if isinstance(ko_table_input, File):
            ko_table: Table = TableImporter.call(File(ko_table_input.path))  # type: ignore
        else:
            ko_table: Table = ko_table_input

        twin_input: Twin = inputs["twin"]
        twin: FlatTwin = twin_input.flatten()
        solver = params["solver"]
        biomass_optimization = params["biomass_optimization"]
        fluxes_to_maximize = params["fluxes_to_maximize"]
        fluxes_to_minimize = params["fluxes_to_minimize"]
        relax_qssa = params["relax_qssa"]
        qssa_relaxation_strength = params["qssa_relaxation_strength"]
        parsimony_strength = params["parsimony_strength"]
        type_ko = params["type_ko"]
        ko_delimiter = params.get_value("ko_delimiter", ",")

        id_column_name = TransformerEntityIDTable.id_column
        ec_number_name = TransformerECNumberTable.ec_number_name

        # If the user provides genes to knockout
        if type_ko == "genes":
            if not ko_table.column_exists(id_column_name):
                raise Exception(
                    f"If your elements to be knocked out are genes, you need to have a column named {id_column_name}"
                )

            genes_to_ko = ko_table.get_column_data(id_column_name)
            dict_gpr_reactions = twin.get_flat_network().network_data._gpr_rxn_ids_map
            dict_reactions_gpr = {value: key for key, value in dict_gpr_reactions.items()}

            df_ko = pd.DataFrame()
            df_genes_reactions = pd.DataFrame()
            for line in genes_to_ko:
                # get the genes
                unique_genes_dict = self.extract_unique_genes(dictionary=dict_reactions_gpr)
                # Modify the dictionary with setting to False the genes provided in input
                line_genes = line.split(ko_delimiter)
                for gene in line_genes:
                    unique_genes_dict[gene] = False

                reactions_to_knockout = []
                # Parse each reaction:
                for reaction in twin.get_flat_network().reactions:
                    rule = twin.get_flat_network().reactions[reaction].gene_reaction_rule
                    if rule != "":
                        # Check if the rule is active
                        is_active = self.is_rule_active(rule=rule, variables=unique_genes_dict)
                        if not is_active:
                            # If the rule is not True, we need to knock out the reaction
                            reactions_to_knockout.append(
                                twin.get_flat_network().reactions[reaction].id
                            )
                # Extend the dataframe
                reactions_to_knockout_str = (
                    ",".join(reactions_to_knockout) if reactions_to_knockout else ""
                )
                line_genes_str = ",".join(line_genes)
                genes_to_knockout = pd.Series(line_genes_str, dtype="str")
                reactions_to_knockout_series = pd.Series(reactions_to_knockout_str, dtype="str")
                # Fill Dataframe for the Table Summary
                df_temp = pd.DataFrame(
                    {
                        "Genes to knockout": genes_to_knockout,
                        "Reactions to knockout": reactions_to_knockout_series,
                    }
                )
                df_genes_reactions = pd.concat([df_genes_reactions, df_temp])
                # Fill Dataframe for the KO Task
                if reactions_to_knockout_str:
                    df_ko_temp = pd.DataFrame({"entity_id": [reactions_to_knockout_str]})
                    df_ko = pd.concat([df_ko, df_ko_temp])

            table_summary = Table(df_genes_reactions)
            # Add column 'entity_id'
            df_ko.rename(columns={0: "entity_id"}, inplace=True)
            # Delete duplicates values
            df_ko = df_ko.drop_duplicates(subset=["entity_id"], keep="first")
            # create ko table entity id
            ko_table = Table(df_ko)
        else:
            table_summary = ko_table
        table_summary.name = "Table summary"

        ko_list: list[str]
        if ko_table.column_exists(id_column_name):
            ko_list = ko_table.get_column_data(id_column_name)
        elif ko_table.column_exists(ec_number_name):
            ko_list = ko_table.get_column_data(ec_number_name)
        else:
            raise Exception(
                f"Missing column {id_column_name} or {ec_number_name}. Please use TransformerEntityIDTable or TransformerECNumberTable."
            )
        # is_monitored_fluxes_expanded = False
        full_ko_result_list = []
        i = 0
        for ko_id in ko_list:
            perc = 100 * (i / ko_table.nb_rows)
            self.update_progress_value(
                perc, message=f"Step {i + 1}/{ko_table.nb_rows}: analyzing knockout '{ko_id}' ..."
            )

            current_ko_twin = twin.copy()
            helper = ReactionKnockOutHelper()
            helper.attach_message_dispatcher(self.message_dispatcher)
            for _, net in current_ko_twin.networks.items():
                _, invalid_ko_ids = helper.knockout_list_of_reactions(
                    net, [ko_id], ko_delimiter=ko_delimiter, inplace=True
                )

            fba_helper = FBAHelper()
            fba_helper.attach_message_dispatcher(self.message_dispatcher)
            current_result: FBAResult = fba_helper.run(
                current_ko_twin,
                solver,
                fluxes_to_maximize,
                fluxes_to_minimize,
                biomass_optimization=biomass_optimization,
                relax_qssa=relax_qssa,
                qssa_relaxation_strength=qssa_relaxation_strength,
                parsimony_strength=parsimony_strength,
            )

            current_fluxes = current_result.get_fluxes_dataframe()

            full_ko_result_list.append({"fluxes": current_fluxes, "invalid_ko_ids": invalid_ko_ids})
            i = i + 1

        koa_result = KOAResult(data=full_ko_result_list, ko_list=ko_list)

        # set simulations
        simulations = []
        for ko_id in ko_list:
            simulations.append(
                {
                    "id": f"{ko_id}",
                    "name": f"KO analysis: {ko_id}",
                    "description": f"Simulation after knockout of reaction(s): {ko_id}",
                }
            )

        # annotate twin
        koa_result.set_simulations(simulations)
        helper = TwinAnnotatorHelper()
        helper.attach_message_dispatcher(self.message_dispatcher)
        twin_output = helper.annotate_from_koa_result(twin_input, koa_result)

        return {"koa_result": koa_result, "twin": twin_output, "table_summary": table_summary}

    # Function to parse values and extract unique elements
    def extract_unique_genes(self, dictionary: dict) -> dict:
        unique_values = {}
        for value in dictionary.values():
            # Remove 'and', 'or', and parentheses, then split by ' '
            elements = (
                value.replace("and", "").replace("or", "").replace("(", "").replace(")", "").split()
            )
            for element in elements:
                unique_values[element] = True
        return unique_values

    # Function to evaluate the gene reaction rule and determine if it's True or not
    def is_rule_active(self, rule: str, variables: dict) -> bool:
        # Replace variable names with their corresponding status in the rule
        for var, status in variables.items():
            rule = rule.replace(var, str(status))
        # Evaluate the modified rule
        try:
            result = eval(rule)
            return result
        except Exception as e:
            print("Error evaluating the rule:", e)
            return False
