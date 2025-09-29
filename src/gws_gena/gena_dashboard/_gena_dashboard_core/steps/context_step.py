import os
import json
import streamlit as st
from typing import Optional
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core import (
    ResourceOrigin, File, Settings, Scenario,
    ProtocolProxy, InputTask, ResourceModel, ScenarioStatus
)
from gws_gena import ContextImporter, ContextBuilder
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import search_context, create_base_scenario_with_tags, search_updated_network, get_context_process_name, display_scenario_parameters
from gws_core.streamlit import StreamlitResourceSelect, StreamlitContainers

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
        context_process = protocol.add_process(
            InputTask, 'selected_context',
            {InputTask.config_name: selected_context.get_resource().get_model_id()}
        )
        protocol.add_output('context_process_output', context_process >> 'resource', flag_resource=False)
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

    url_doc_context = "https://constellab.community/bricks/gws_gena/latest/doc/technical-folder/resource/Context"
    url_doc_context_importer = "https://constellab.community/bricks/gws_gena/latest/doc/technical-folder/task/ContextImporter"
    url_doc_context_builder = "https://constellab.community/bricks/gws_gena/latest/doc/technical-folder/task/ContextBuilder"
    translate_service = gena_state.get_translate_service()

    col_question, col_help = StreamlitContainers.columns_with_fit_content('container-column_context', cols=[1, 'fit-content'],
        vertical_align_items='center')
    with col_question:
        st.selectbox(
            translate_service.translate("would_like_add_context"),
            options=[translate_service.translate("yes"), translate_service.translate("no")],
            index=None,
            key=gena_state.CONTEXT_BOOL_KEY
        )
    with col_help:
        st.link_button("**?**", url_doc_context)

    context_choice = gena_state.get_context_bool()

    if context_choice == translate_service.translate("no"):
        st.info(translate_service.translate("run_context_importer_info"))
        return True

    elif context_choice == translate_service.translate("yes"):
        st.selectbox(
            translate_service.translate("how_provide_context_data"),
            options=[translate_service.translate("select_existing_context"), translate_service.translate("build_new_context")],
            index=None,
            key=gena_state.CONTEXT_OPTION_KEY
        )

        context_option = gena_state.get_context_option()

        if context_option == translate_service.translate("select_existing_context"):
            col_select, col_help = StreamlitContainers.columns_with_fit_content('container-column_context_importer', cols=[1, 'fit-content'],
                vertical_align_items='center')
            with col_select:
                resource_select = StreamlitResourceSelect()
                resource_select.select_resource(
                    placeholder=translate_service.translate('search_context_resource'),
                    key=gena_state.RESOURCE_SELECTOR_CONTEXT_KEY,
                    defaut_resource=None
                )
            with col_help:
                st.link_button("**?**", url_doc_context_importer)
            return bool(gena_state.get_resource_selector_context())

        elif context_option == translate_service.translate("build_new_context"):
            col_info, col_help = StreamlitContainers.columns_with_fit_content('container-column_context_builder', cols=[1, 'fit-content'],
                vertical_align_items='center')
            with col_info:
                st.info(translate_service.translate("contextualise_network_info"))
            with col_help:
                st.link_button("**?**", url_doc_context_builder)
            # Phenotype table selector
            resource_select_phenotype = StreamlitResourceSelect()
            resource_select_phenotype.select_resource(
                placeholder=translate_service.translate('search_phenotype_table'),
                key=gena_state.RESOURCE_SELECTOR_PHENOTYPE_KEY,
                defaut_resource=None
            )

            # Flux table selector
            resource_select_flux = StreamlitResourceSelect()
            resource_select_flux.select_resource(
                placeholder=translate_service.translate('search_flux_table'),
                key=gena_state.RESOURCE_SELECTOR_FLUX_KEY,
                defaut_resource=None
            )

            return (gena_state.get_resource_selector_phenotype() or
                    gena_state.get_resource_selector_flux())
        else:
            st.info(translate_service.translate("please_select_option"))
            return False
    else:
        st.info(translate_service.translate("please_select_option"))
        return False


def render_context_step(selected_scenario: Optional[Scenario], gena_state: State) -> None:
    """Main function to render the context step."""
    if not selected_scenario:
        _render_context_creation_ui(gena_state)
    else:
        _render_context_results(selected_scenario, gena_state)


def _render_context_creation_ui(gena_state: State) -> None:
    """Render UI for creating a new context scenario."""
    translate_service = gena_state.get_translate_service()
    # Check if network is available
    file_network = search_updated_network(gena_state)
    if not file_network:
        st.info(translate_service.translate("save_network_proceed"))
        return

    if gena_state.get_is_standalone():
        return

    # Render setup UI
    if not _render_context_setup_ui(gena_state):
        return

    st.info(f"ℹ️ {translate_service.translate('context_note')}")

    # Run context importer button
    if st.button(translate_service.translate("run_context_importer"), icon=":material/play_arrow:", use_container_width=False):
        context_choice = gena_state.get_context_bool()

        if context_choice == translate_service.translate("no"):
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
                st.warning(translate_service.translate("select_resource_warning"))
                return

            # Create scenario
            scenario = create_base_scenario_with_tags(
                gena_state, gena_state.TAG_CONTEXT,
                f"{gena_state.get_current_analysis_name()} - Context"
            )
            protocol = scenario.get_protocol()

            context_option = gena_state.get_context_option()

            if context_option == translate_service.translate("build_new_context"):
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
    translate_service = gena_state.get_translate_service()
    st.markdown(f"##### {translate_service.translate('context_results')}")

    # Display parameters reminder
    process_name = get_context_process_name(selected_scenario)
    display_scenario_parameters(selected_scenario, process_name, gena_state)

    if selected_scenario.status != ScenarioStatus.SUCCESS:
        return

    context_output = search_context(gena_state)

    if context_output:
        st.json(context_output.dumps())
        st.json(context_output.dumps())
