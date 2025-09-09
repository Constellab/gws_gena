import os
import json
import streamlit as st
from typing import Optional, Tuple

from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core import (
    ResourceOrigin, File, Settings, ResourceSet, Scenario, ScenarioProxy,
    ProtocolProxy, InputTask, ProcessProxy, ResourceModel, ScenarioStatus
)
from gws_gena import ContextImporter, ContextBuilder
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import search_context, create_base_scenario_with_tags, search_updated_network
from gws_core.streamlit import StreamlitResourceSelect

def _create_empty_context_resource(gena_state: State) -> ResourceModel:
    """Create an empty context resource file."""
    path_temp = os.path.join(os.path.abspath(os.path.dirname(__file__)), Settings.make_temp_dir())
    full_path = os.path.join(path_temp, f"{gena_state.get_current_analysis_name()}_empty_context.json")

    content = {"name": "empty_context", 'measures': []}

    with open(full_path, 'w') as f:
        json.dump(content, f, indent=4)

    context_file = File(full_path)
    return ResourceModel.save_from_resource(context_file, origin=ResourceOrigin.UPLOADED, flagged=True)


def _handle_context_builder(protocol: ProtocolProxy, gena_state: State) -> None:
    """Handle context builder workflow with phenotype and/or flux tables."""
    selected_phenotype = None
    selected_flux = None

    if gena_state.get_resource_selector_phenotype():
        selected_phenotype_id = gena_state.get_resource_selector_phenotype()["resourceId"]
        selected_phenotype = ResourceModel.get_by_id(selected_phenotype_id)

    if gena_state.get_resource_selector_flux():
        selected_flux_id = gena_state.get_resource_selector_flux()["resourceId"]
        selected_flux = ResourceModel.get_by_id(selected_flux_id)

    # Add network resource
    network_resource = protocol.add_process(
        InputTask, 'network_resource',
        {InputTask.config_name: gena_state.get_resource_id_network()}
    )

    # Add context builder process
    context_process = protocol.add_process(ContextBuilder, 'context_builder_process')
    protocol.add_connector(network_resource >> 'resource', context_process << 'network')

    # Add phenotype resource if selected
    if selected_phenotype:
        phenotype_resource = protocol.add_process(
            InputTask, 'phenotype_resource',
            {InputTask.config_name: selected_phenotype.get_resource().get_model_id()}
        )
        protocol.add_connector(phenotype_resource >> 'resource', context_process << 'pheno_table')

    # Add flux resource if selected
    if selected_flux:
        flux_resource = protocol.add_process(
            InputTask, 'flux_resource',
            {InputTask.config_name: selected_flux.get_resource().get_model_id()}
        )
        protocol.add_connector(flux_resource >> 'resource', context_process << 'flux_table')

    # Add output
    protocol.add_output('context_process_output', context_process >> 'context', flag_resource=False)


def _handle_existing_context(protocol: ProtocolProxy, gena_state: State) -> bool:
    """Handle existing context resource selection. Returns True if context is already processed."""
    selected_context_id = gena_state.get_resource_selector_context()["resourceId"]
    selected_context = ResourceModel.get_by_id(selected_context_id)

    if selected_context.resource_typing_name == 'RESOURCE.gws_gena.Context':
        # Context is already processed, just add as input
        protocol.add_process(
            InputTask, 'selected_context',
            {InputTask.config_name: selected_context.get_resource().get_model_id()}
        )
        return True

    # Context needs to be imported
    _add_context_importer(protocol, selected_context)
    return False


def _add_context_importer(protocol: ProtocolProxy, context_resource_model: ResourceModel) -> None:
    """Add context importer process to the protocol."""
    context_resource = protocol.add_process(
        InputTask, 'selected_context',
        {InputTask.config_name: context_resource_model.get_resource().get_model_id()}
    )

    context_process = protocol.add_process(ContextImporter, 'context_importer_process')
    protocol.add_connector(context_resource >> 'resource', context_process << 'source')
    protocol.add_output('context_process_output', context_process >> 'target', flag_resource=False)


def _render_context_setup_ui(gena_state: State) -> bool:
    """Render the context setup UI and return True if ready to proceed."""
    st.selectbox(
        "Would you like to add a context?",
        options=["Yes", "No"],
        index=None,
        key=gena_state.CONTEXT_BOOL_KEY
    )

    context_choice = gena_state.get_context_bool()

    if context_choice == "No":
        st.info("You can directly run context importer. Context will be empty.")
        return True

    elif context_choice == "Yes":
        st.selectbox(
            "How would you like to provide context data?",
            options=["Select existing context resource", "Build a new context"],
            index=None,
            key=gena_state.CONTEXT_OPTION_KEY
        )

        context_option = gena_state.get_context_option()

        if context_option == "Select existing context resource":
            resource_select = StreamlitResourceSelect()
            resource_select.select_resource(
                placeholder='Search for context resource',
                key=gena_state.RESOURCE_SELECTOR_CONTEXT_KEY,
                defaut_resource=None
            )
            return bool(gena_state.get_resource_selector_context())

        elif context_option == "Build a new context":
            st.info("In order to contextualise the network, you must select either a phenotype or a flux table.")

            # Phenotype table selector
            resource_select_phenotype = StreamlitResourceSelect()
            resource_select_phenotype.select_resource(
                placeholder='Search for phenotype table resource',
                key=gena_state.RESOURCE_SELECTOR_PHENOTYPE_KEY,
                defaut_resource=None
            )

            # Flux table selector
            resource_select_flux = StreamlitResourceSelect()
            resource_select_flux.select_resource(
                placeholder='Search for flux table resource',
                key=gena_state.RESOURCE_SELECTOR_FLUX_KEY,
                defaut_resource=None
            )

            return (gena_state.get_resource_selector_phenotype() or
                    gena_state.get_resource_selector_flux())
        else:
            st.info("Please select an option.")
            return False
    else:
        st.info("Please select an option.")
        return False


def render_context_step(selected_scenario: Optional[Scenario], gena_state: State) -> None:
    """Main function to render the context step."""
    if not selected_scenario:
        _render_context_creation_ui(gena_state)
    else:
        _render_context_results(selected_scenario, gena_state)


def _render_context_creation_ui(gena_state: State) -> None:
    """Render UI for creating a new context scenario."""
    # Check if network is available
    file_network = search_updated_network(gena_state)
    if not file_network:
        st.info("Please save a network to proceed.")
        return

    if gena_state.get_is_standalone():
        return

    # Render setup UI
    if not _render_context_setup_ui(gena_state):
        return

    st.info("Please note that once you have run the context importer, you will not be able to modify the network.")

    # Run context importer button
    if st.button("Run context importer", icon=":material/play_arrow:", use_container_width=False):
        context_choice = gena_state.get_context_bool()

        if context_choice == "No":
            # Create empty context scenario
            selected_context = _create_empty_context_resource(gena_state)
            scenario = create_base_scenario_with_tags(
                gena_state, gena_state.TAG_CONTEXT,
                f"{gena_state.get_current_analysis_name()} - Context"
            )
            protocol = scenario.get_protocol()
            _add_context_importer(protocol, selected_context)

        else:
            # Validate resource selection
            if not any([
                gena_state.get_resource_selector_phenotype(),
                gena_state.get_resource_selector_flux(),
                gena_state.get_resource_selector_context()
            ]):
                st.warning("Please select at least one resource.")
                return

            # Create scenario
            scenario = create_base_scenario_with_tags(
                gena_state, gena_state.TAG_CONTEXT,
                f"{gena_state.get_current_analysis_name()} - Context"
            )
            protocol = scenario.get_protocol()

            context_option = gena_state.get_context_option()

            if context_option == "Build a new context":
                _handle_context_builder(protocol, gena_state)
            else:  # Select existing context resource
                if _handle_existing_context(protocol, gena_state):
                    # Context is already processed, no need for importer
                    pass

        # Queue scenario and refresh UI
        scenario.add_to_queue()
        gena_state.reset_tree_analysis()
        gena_state.set_tree_default_item(scenario.get_model_id())
        st.rerun()


def _render_context_results(selected_scenario: Scenario, gena_state: State) -> None:
    """Render context results for a completed scenario."""
    st.markdown("##### Context Results")

    if selected_scenario.status != ScenarioStatus.SUCCESS:
        return

    context_output = search_context(gena_state)

    if context_output:
        st.json(context_output.dumps())
