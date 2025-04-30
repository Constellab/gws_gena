
from typing import List

from gws_core import (BoolParam, ConfigParams, FloatParam, InputSpec,
                      InputSpecs, IntParam, ListParam, OutputSpec, OutputSpecs,
                      StrParam, Table, TableConcatHelper, Task, TaskInputs,
                      TaskOutputs, TypingStyle, task_decorator)
from gws_gena.fba.fba_result import FBAResult
from gws_gena.fba.fba_helper.fba_helper_v2 import FBAHelperV2
from gws_gena.twin.helper.twin_annotator_helper_v2 import TwinAnnotatorHelperV2
from gws_gena.twin.helper.twin_helper_v2 import TwinHelperV2
from gws_gena.twin.twin_v2 import TwinV2
from gws_gena.network.network_cobra import NetworkCobra
from cobra.core import Metabolite
from gws_biota import Compartment as BiotaCompartment

@task_decorator("FBAV2", human_name="FBA V2", short_description="Flux balance analysis",
                style=TypingStyle.community_icon(icon_technical_name="cone", background_color="#d9d9d9"))
class FBAV2(Task):
    """
    FBA task class

    Performs Flux Balance Analysis from a digital twin.

    A digital twin is a mathematical representation of the metabolic interactions involved in a living cell or microbial organism
    (e.g. animal cell, bacteria, fungus, etc.).

    You need to provide your twin in the input and you can set some parameters. The most important is to choose whether you want to maximize or minimize the biomass flux.
    Then, you can add other fluxes to optimize (fluxes to maximize and fluxes to minimize), the solver and some parameters related to the solver method.
    The last parameter "Number of simulations" allows you to run multiple simulations of FBA using your context with multi target values.

    In output you will get your twin annotated and two tables with the estimated fluxes.
    """

    input_specs = InputSpecs({'twin': InputSpec(TwinV2, human_name="Digital twin",
                             short_description="The digital twin to analyze")})
    output_specs = OutputSpecs({
        'twin': OutputSpec(TwinV2, human_name="Simulated digital twin", short_description="The simulated digital twin"),
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
            allowed_values=["quad", "highs-ds",
                            "highs-ipm", "highs", "interior-point"],
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
            default_value=None, min_value=1, optional=True, visibility=StrParam.PROTECTED_VISIBILITY,
            human_name="Number of simulations",
            short_description="Set the number of simulations to perform. You must provide at least the same number of measures in the context. By default, keeps all simulations."),
        "biomass_metabolite_id_user":
        StrParam(
            default_value="", human_name="Biomass metabolite id",
            short_description="The id of the Biomass metabolite", optional=True),
        "add_biomass":
        BoolParam(
            human_name="Add biomass metabolite", default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Add biomass metabolite in a compartment biomass.")
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        biomass_metabolite_id_user = params.get_value("biomass_metabolite_id_user", None)
        add_biomass = params.get_value("add_biomass", False)
        if (add_biomass is True and biomass_metabolite_id_user):
            raise Exception(
                "If there is already a biomass metabolite in the network, we can't add one. Set the parameter 'add_biomass' to False")
        if (add_biomass is False and not biomass_metabolite_id_user):
            raise Exception(
                "A biomass metabolite must be present in the network. Set the biomass_metabolite_id_user parameter with your metabolite or set add_biomass to True.")

        twin: TwinV2 = inputs["twin"]

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

        network = twin.get_network()
        network = manage_biomass(network,biomass_metabolite_id_user = biomass_metabolite_id_user, add_biomass = add_biomass)
        network = add_environnement_compartment(network)
        twin_env = TwinV2()
        twin_env.set_context(twin.get_context())
        twin_env.set_network(network)

        # retrieve the context of the twin
        context = twin_env.get_context()

        number_of_simulations = params["number_of_simulations"]
        # If number_of_simulations is not provided, keep all the simulations
        if number_of_simulations is None:
            number_of_simulations = next(
                (len(measure.target) for _, measure in context.reaction_data.items()), None)

        # check the length of the values
        for name_measure, measure in context.reaction_data.items():
            if len(measure.target) < number_of_simulations:
                raise Exception(
                    "The number of target values must be at least equal to the number of simulations. For " +
                    name_measure + ", there are " + str(len(measure.target)) +
                    " values of targets while the number of simulations is set to " + str(number_of_simulations))
            if len(measure.upper_bound) < number_of_simulations:
                raise Exception(
                    "The number of upper bound values must be at least equal to the number of simulations. For " +
                    name_measure + ", there are " + str(len(measure.upper_bound)) +
                    " values of upper bound while the number of simulations is set to " +
                    str(number_of_simulations))
            if len(measure.lower_bound) < number_of_simulations:
                raise Exception(
                    "The number of lower bound values must be at least equal to the number of simulations. For " +
                    name_measure + ", there are " + str(len(measure.lower_bound)) +
                    " values of lower_bound while the number of simulations is set to " +
                    str(number_of_simulations))
            if len(measure.confidence_score) < number_of_simulations:
                raise Exception(
                    "The number of confidence score values must be at least equal to the number of simulations. For " +
                    name_measure + ", there are " + str(len(measure.confidence_score)) +
                    " values of confidence score while the number of simulations is set to " +
                    str(number_of_simulations))

        fba_results: List[FBAResult] = []

        # If number of simulations is not None, there is a context with simulations
        if (number_of_simulations):
            # run through the number of simulations
            for i in range(0, number_of_simulations):
                new_twin = TwinHelperV2.build_twin_from_sub_context(twin_env, i)
                fba_results.append(self.call_fba(new_twin, params))
                self.update_progress_value(((i+1) / number_of_simulations) * 100,
                                           message="Running FBA for all simulations")
        else:  # if number of simulations is None, there is no context provided, so we run only one FBA
            new_twin = TwinHelperV2.build_twin_from_sub_context(twin_env, 0)
            fba_results.append(self.call_fba(new_twin, params))
            self.update_progress_value(100, message="Running FBA")

        self.log_info_message('Annotating the twin')
        annotator_helper = TwinAnnotatorHelperV2()
        annotator_helper.attach_message_dispatcher(self.message_dispatcher)
        result_twin = annotator_helper.annotate_from_fba_results(
            twin_env, fba_results)

        self.log_info_message('Merging all fba results')
        # merge all fba results
        self.log_info_message('Creating lists')
        flux_tables: List[Table] = []
        sv_tables: List[Table] = []
        for fba_result in fba_results:
            flux_tables.append(fba_result.get_flux_table())
            sv_tables.append(fba_result.get_sv_table())
        self.log_info_message('Concat flux table')
        merged_flux_table: Table = TableConcatHelper.concat_table_rows(
            flux_tables)
        self.log_info_message('Concat sv table')
        merged_sv_table: Table = TableConcatHelper.concat_table_rows(sv_tables)
        self.log_info_message('Create FBAResult')
        merged_fba_result = FBAResult(
            merged_flux_table.get_data(), merged_sv_table.get_data())

        return {
            "fba_result": merged_fba_result,
            "twin": result_twin
        }

    def call_fba(self, twin: TwinV2, params: ConfigParams) -> FBAResult:

        # Run the FBA for this twin
        fba_helper = FBAHelperV2()
        # fba_helper.attach_task(self)
        fba_result = fba_helper.run(
            twin, solver=params["solver"],
            fluxes_to_maximize=params["fluxes_to_maximize"],
            fluxes_to_minimize=params["fluxes_to_minimize"],
            biomass_optimization=params["biomass_optimization"],
            relax_qssa=params["relax_qssa"],
            qssa_relaxation_strength=params["qssa_relaxation_strength"],
            parsimony_strength=params["parsimony_strength"])

        return fba_result
