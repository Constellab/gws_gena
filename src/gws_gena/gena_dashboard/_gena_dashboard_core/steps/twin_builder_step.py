import streamlit as st
from gws_core import InputTask, Scenario, ScenarioProxy, ScenarioStatus, Tag
from gws_gena import TwinBuilder
from gws_streamlit_main import StreamlitContainers

from ..functions_steps import (
    create_base_scenario_with_tags,
    display_network,
    display_scenario_parameters,
    extract_network_and_context_from_twin,
)
from ..state import State


def twin_builder_run(gena_state: State):
    scenario = create_base_scenario_with_tags(
        gena_state,
        gena_state.TAG_TWIN_BUILDER,
        f"{gena_state.get_current_analysis_name()} - Twin Builder",
    )
    scenario.add_tag(
        Tag(
            gena_state.TAG_TWIN_BUILDER_ID,
            scenario.get_model_id(),
            is_propagable=False,
            auto_parse=True,
        )
    )
    protocol = scenario.get_protocol()

    # Add twin builder process
    twin_process = protocol.add_process(TwinBuilder, "twin_process")

    # Retrieve context output and connect

    context_resource = protocol.add_process(
        InputTask, "context_resource", {InputTask.config_name: gena_state.get_resource_id_context()}
    )
    protocol.add_connector(
        out_port=context_resource >> "resource", in_port=twin_process << "context"
    )

    network_resource = protocol.add_process(
        InputTask, "network_resource", {InputTask.config_name: gena_state.get_resource_id_network()}
    )
    protocol.add_connector(
        out_port=network_resource >> "resource", in_port=twin_process << "network"
    )

    # Add outputs
    protocol.add_output("twin_output", twin_process >> "twin", flag_resource=False)

    scenario.add_to_queue()
    gena_state.reset_tree_analysis()
    gena_state.set_tree_default_item(scenario.get_model_id())


def render_twin_builder_step(selected_scenario: Scenario, gena_state: State) -> None:
    translate_service = gena_state.get_translate_service()
    if not selected_scenario:
        if not gena_state.get_is_standalone():
            col_run, col_help = StreamlitContainers.columns_with_fit_content(
                "container-column_twin_builder",
                cols=[1, "fit-content"],
                vertical_align_items="center",
            )

            with col_help:
                url_doc_twin_builder = "https://constellab.community/bricks/gws_gena/latest/doc/technical-folder/task/TwinBuilder"
                st.link_button("**?**", url_doc_twin_builder)
            with col_run:
                # On click, open a dialog to allow the user to select params of twin builder
                st.button(
                    translate_service.translate("run_twin_builder"),
                    icon=":material/play_arrow:",
                    width="stretch",
                    on_click=lambda state=gena_state: twin_builder_run(state),
                )
    else:
        # Display details about scenario twin builder
        st.markdown(f"##### {translate_service.translate('twin_builder_scenario_results')}")
        display_scenario_parameters(selected_scenario, "twin_process", gena_state)
        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        twin_resource_set_dict = (
            protocol_proxy.get_process("twin_process").get_output("twin").get_resources()
        )
        network_resource, context_resource = extract_network_and_context_from_twin(
            twin_resource_set_dict
        )

        tab_network, tab_context = st.tabs(
            [translate_service.translate("network"), translate_service.translate("context")]
        )
        with tab_network:
            display_network(network_resource.get_model_id())
        with tab_context:
            st.json(context_resource.dumps())
