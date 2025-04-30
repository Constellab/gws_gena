
from typing import List
from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, StrParam, Table, Task, TaskInputs,
                      TaskOutputs, TypingStyle, task_decorator)

import pandas as pd

from gws_gena.fba.fba_v2 import FBAV2
from gws_gena.fba.fba_helper.fba_helper_v2 import FBAHelperV2
from gws_gena.twin.helper.twin_annotator_helper_v2 import TwinAnnotatorHelperV2
from gws_gena.twin.twin_v2 import TwinV2
from gws_gena.network.reaction.helper.reaction_knockout_helper_v2 import \
    ReactionKnockOutHelperV2
from ..data.task.transformer_ec_number_table import TransformerECNumberTable
from ..data.task.transformer_entity_id_table import TransformerEntityIDTable
from ..fba.fba_result import FBAResult
from .koa_result import KOAResult
from gws_gena.network.network_cobra import NetworkCobra
from cobra.core import Metabolite
from gws_biota import Compartment as BiotaCompartment


@task_decorator("KOAV2", human_name="KOA V2", short_description="Knockout Analysis",
                style=TypingStyle.material_icon(material_icon_name="delete_forever", background_color="#d9d9d9"))
class KOAV2(Task):
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

    input_specs = InputSpecs({
        'twin': InputSpec(TwinV2, human_name="Digital twin", short_description="The digital twin to analyze"),
        'ko_table': InputSpec(Table, human_name="KO table", short_description="The table of KO hypotheses"),
    })
    output_specs = OutputSpecs({
        'twin': OutputSpec(TwinV2, human_name="Simulated digital twin", short_description="The simulated digital twin"),
        'koa_result': OutputSpec(KOAResult, human_name="KOA result tables", short_description="The KOA result tables"),
        'table_summary' : OutputSpec(Table, human_name="Table Summary", short_description="The table summarising the reactions knocked out")
    })
    config_specs = {
        **FBAV2.config_specs,
        'ko_delimiter':
        StrParam(
            default_value=",", human_name="Multiple KO delimiter",
            short_description="The delimiter used to separate IDs or EC numbers when multiple KO are performed"),
        'type_ko':
        StrParam(allowed_values=["reactions", "genes"],
                 default_value="reactions", human_name="Type of elements to knock-out",
                 short_description="The type of elements provided to knock-out: reactions or genes")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        ko_table: Table = inputs["ko_table"]
        twin_original: TwinV2 = inputs["twin"]
        solver = params["solver"]
        biomass_optimization = params["biomass_optimization"]
        fluxes_to_maximize = params["fluxes_to_maximize"]
        fluxes_to_minimize = params["fluxes_to_minimize"]
        relax_qssa = params["relax_qssa"]
        qssa_relaxation_strength = params["qssa_relaxation_strength"]
        parsimony_strength = params["parsimony_strength"]
        type_ko = params["type_ko"]
        ko_delimiter = params.get_value("ko_delimiter", ",")

        biomass_metabolite_id_user = params.get_value("biomass_metabolite_id_user", None)
        add_biomass = params.get_value("add_biomass", False)
        if (add_biomass is True and biomass_metabolite_id_user):
            raise Exception(
                "If there is already a biomass metabolite in the network, we can't add one. Set the parameter 'add_biomass' to False")
        if (add_biomass is False and not biomass_metabolite_id_user):
            raise Exception(
                "A biomass metabolite must be present in the network. Set the biomass_metabolite_id_user parameter with your metabolite or set add_biomass to True.")

        #Act on the network to add environnement compartment
        def add_environnement_compartment(network : NetworkCobra):
            model = network.get_cobra_model()
            BIGG_REACTION_PREFIX_TO_IGNORE = ["EX_", "DM_"]
            list_to_keep = []
            for i, rxn_data in enumerate(network.get_reactions()):
                to_keep = True
                for pref in BIGG_REACTION_PREFIX_TO_IGNORE:
                    if rxn_data.id.startswith(pref):
                        if pref == "EX_":
                            metabolite = next(iter(rxn_data.metabolites)).id
                            # Add compartment environment
                            if isinstance(network.get_compartments(), dict):  # If there is the first loading
                                # Create a new metabolite with the suffix "_env"
                                new_metabolite_id = metabolite.split("_e")[0] + "_env"
                                # Check if the new metabolite is already in the data["metabolites"]
                                metabolite_found = network.has_metabolite(new_metabolite_id)
                                if not metabolite_found:
                                    # Create a new metabolite
                                    new_metabolite = Metabolite(id=new_metabolite_id, name=new_metabolite_id,compartment='env')
                                    # Add the new metabolite to the reaction
                                    reaction_cobra = model.reactions.get_by_id(rxn_data.id)
                                    reaction_cobra.add_metabolites({new_metabolite: 1.0})
                                    # Add this metabolite to the reaction EX_
                                    model.compartments = {"env": {'id': 'env', 'go_id': 'GO:0005576', 'name': 'extracellular region (environment)'}}
                                    #network.set_compartments({"env": {'id': 'env', 'go_id': 'GO:0005576', 'name': 'extracellular region (environment)'}})
                        else:
                            to_keep = False
                            break
                if to_keep:
                    list_to_keep.append(i)

            nb_ignored_rxns = len(network.get_reactions()) - len(list_to_keep)
            if nb_ignored_rxns > 0:
                self.log_info_message(f"{nb_ignored_rxns} reactions with prefixes {BIGG_REACTION_PREFIX_TO_IGNORE} were ignored")
                rxn_data = [network.get_reactions()[i] for i in list_to_keep]
                #network.add_reactions(rxn_data)
                model.add_reactions(rxn_data)

            network.set_cobra_model(model)
            return network

        def manage_biomass(net: "NetworkCobra", biomass_metabolite_id_user: str = None, add_biomass: bool = False):
            if biomass_metabolite_id_user != "":
                if not net.has_metabolite(biomass_metabolite_id_user):
                    # if the metabolite doesn't exist in the network, raises an error
                    raise Exception(f"The metabolite {biomass_metabolite_id_user} doesn't exist in the network.")
                else:
                    # Check if the metabolite produced by the reaction is in the biomass compartment
                    compartment = net.get_metabolite_by_id_and_check(biomass_metabolite_id_user).compartment
                    compartment_go_id = BiotaCompartment.get_by_bigg_id(compartment).go_id
                    if compartment_go_id != 'GO:0016049':
                        # If not, raise an Exception
                        raise Exception(f"The metabolite {biomass_metabolite_id_user} must be in the biomass compartment")

                    # Check if the metabolite biomass is not used in another reaction as a substrate
                    for reaction_id in net.get_reaction_ids():
                        reaction = net.get_reaction_by_id_and_check(reaction_id)
                        # Check if the biomass metabolite is a reactant in the current reaction
                        if biomass_metabolite_id_user in [met.id for met in reaction.reactants]:
                            raise ValueError(
                                f"The metabolite {biomass_metabolite_id_user} can't be used in the reaction {reaction_id}. Verify your biomass_metabolite_id.")

            elif add_biomass:
                if net.get_biomass_metabolite() is None:
                    for reaction in net.get_reaction_ids():
                        if "biomass" in reaction.lower():
                            # can be used as biomass reaction
                            biomass = Metabolite(id = "biomass", name="biomass", compartment='b')
                            model = net.get_cobra_model()
                            reaction_cobra = model.reactions.get_by_id(reaction)
                            reaction_cobra.add_metabolites({biomass: 1})
                            self.log_warning_message(
                                f'Reaction "{reaction_cobra.id} ({reaction_cobra.name})" was automatically inferred as biomass reaction')
                            net.set_cobra_model(model)
            return net

        network = twin_original.get_network()
        network = manage_biomass(network,biomass_metabolite_id_user = biomass_metabolite_id_user, add_biomass = add_biomass)
        network = add_environnement_compartment(network)
        twin = TwinV2()
        twin.set_context(twin_original.get_context())
        twin.set_network(network)


        id_column_name = TransformerEntityIDTable.id_column
        ec_number_name = TransformerECNumberTable.ec_number_name

        ### If the user provides genes to knockout
        if type_ko == "genes":
            if not ko_table.column_exists(id_column_name):
                raise Exception(f"If your elements to be knocked out are genes, you need to have a column named {id_column_name}")

            genes_to_ko = ko_table.get_column_data(id_column_name)
            dict_reactions_gpr = twin.get_network().get_reactions_gpr_dict()

            df_ko = pd.DataFrame()
            df_genes_reactions = pd.DataFrame()
            for line in genes_to_ko:
                # get the genes
                unique_genes_dict = self.extract_unique_genes(dictionary = dict_reactions_gpr)
                # Modify the dictionary with setting to False the genes provided in input
                line = line.split(ko_delimiter)
                for gene in line:
                    unique_genes_dict[gene] = False

                reactions_to_knockout = []
                # Parse each reaction:
                for reaction in twin.get_network().get_reactions_dict():
                    rule = twin.get_network().get_reaction_by_id_and_check(reaction).gene_reaction_rule
                    if rule != "":
                        # Check if the rule is active
                        is_active = self.is_rule_active(rule = rule, variables = unique_genes_dict)
                        if not is_active:
                            # If the rule is not True, we need to knock out the reaction
                            rxn_to_ko = twin.get_network().network_dict['name'] + "_" + twin.get_network().get_reaction_by_id_and_check(reaction).id
                            reactions_to_knockout.append(rxn_to_ko)
                # Extend the dataframe
                if reactions_to_knockout:
                    reactions_to_knockout = ','.join(reactions_to_knockout)
                line = ','.join(line)
                genes_to_knockout = pd.Series(line, dtype='str')
                reactions_to_knockout = pd.Series(reactions_to_knockout, dtype='str')
                #Fill Dataframe for the Table Summary
                df_temp = pd.DataFrame({'Genes to knockout': genes_to_knockout,'Reactions to knockout': reactions_to_knockout})
                df_genes_reactions = pd.concat([df_genes_reactions, df_temp])
                #Fill Dataframe for the KO Task
                df_ko = pd.concat([df_ko, reactions_to_knockout])

            table_summary = Table(df_genes_reactions)
            # Add column 'entity_id'
            df_ko.rename(columns={0: 'entity_id'}, inplace=True)
            #Delete duplicates values
            df_ko = df_ko.drop_duplicates(subset=['entity_id'],keep='first')
            # create ko table entity id
            ko_table = Table(df_ko)
        else:
            table_summary = ko_table
        table_summary.name = "Table summary"

        ko_list: List[str]
        if ko_table.column_exists(id_column_name):
            ko_list = ko_table.get_column_data(id_column_name)
        elif ko_table.column_exists(ec_number_name):
            ko_list = ko_table.get_column_data(ec_number_name)
        else:
            raise Exception(f'Missing column {id_column_name} or {ec_number_name}. Please use TransformerEntityIDTable or TransformerECNumberTable.')
        # is_monitored_fluxes_expanded = False
        full_ko_result_list = []
        i = 0
        for ko_id in ko_list:
            perc = 100 * (i/ko_table.nb_rows)
            self.update_progress_value(
                perc, message=f"Step {i+1}/{ko_table.nb_rows}: analyzing knockout '{ko_id}' ...")

            current_ko_twin = twin.set_model_name_twin()
            helper = ReactionKnockOutHelperV2()
            helper.attach_message_dispatcher(self.message_dispatcher)
            _, invalid_ko_ids = helper.knockout_list_of_reactions(current_ko_twin.get_network(), [ko_id], ko_delimiter=ko_delimiter, inplace=True)

            fba_helper = FBAHelperV2()
            fba_helper.attach_message_dispatcher(self.message_dispatcher)
            current_result: FBAResult = fba_helper.run(
                twin, solver, fluxes_to_maximize, fluxes_to_minimize,
                biomass_optimization=biomass_optimization,
                relax_qssa=relax_qssa,
                qssa_relaxation_strength=qssa_relaxation_strength,
                parsimony_strength=parsimony_strength)

            current_fluxes = current_result.get_fluxes_dataframe()

            full_ko_result_list.append({
                "fluxes": current_fluxes,
                "invalid_ko_ids": invalid_ko_ids
            })
            i = i + 1

        koa_result = KOAResult(data=full_ko_result_list,ko_list=ko_list)

        # set simulations
        simulations = []
        for ko_id in ko_list:
            simulations.append({
                "id": f"{ko_id}",
                "name": f"KO analysis: {ko_id}",
                "description": f"Simulation after knockout of reaction(s): {ko_id}"
            })

        # annotate twin
        koa_result.set_simulations(simulations)
        helper_annotator = TwinAnnotatorHelperV2()
        helper_annotator.attach_message_dispatcher(self.message_dispatcher)
        twin = helper_annotator.annotate_from_koa_result(inputs["twin"], koa_result)

        return {
            "koa_result": koa_result,
            "twin": twin,
            "table_summary" : table_summary
        }

    # Function to parse values and extract unique elements
    def extract_unique_genes(self, dictionary : dict) -> dict:
        unique_values = {}
        for value in dictionary.values():
            # Remove 'and', 'or', and parentheses, then split by ' '
            elements = value.replace('and', '').replace('or', '').replace('(', '').replace(')', '').split()
            for element in elements:
                unique_values[element] = True
        return unique_values

    # Function to evaluate the gene reaction rule and determine if it's True or not
    def is_rule_active(self, rule : str, variables : dict) -> bool:
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
