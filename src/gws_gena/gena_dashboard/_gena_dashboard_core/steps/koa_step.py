import os
import streamlit as st
import pandas as pd
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import FrontService, FsNodeExtractor, Scenario, ScenarioProxy, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_gena import KOA
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("KOA parameters")
def dialog_koa_params(gena_state: State):
    st.text_input("KOA Analysis scenario name:", placeholder="Enter KOA analysis scenario name", value=f"{gena_state.get_current_analysis_name()} - KOA Analysis", key=gena_state.FUNCTIONAL_ANALYSIS_SCENARIO_NAME_INPUT_KEY)
    form_config = StreamlitTaskRunner(KOA)
    form_config.generate_config_form_without_run(
        session_state_key=gena_state.FUNCTIONAL_ANALYSIS_CONFIG_KEY,
        default_config_values=KOA.config_specs.get_default_values(),
        is_default_config_valid=KOA.config_specs.mandatory_values_are_set(
            KOA.config_specs.get_default_values()))

    if st.button("Run KOA Analysis", use_container_width=True, icon=":material/play_arrow:", key="button_koa"):
        if not gena_state.get_koa_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(gena_state, gena_state.TAG_KOA, gena_state.get_scenario_user_name(gena_state.KOA_SCENARIO_NAME_INPUT_KEY))
            feature_scenario_id = gena_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(gena_state.TAG_TWIN_BUILDER_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(gena_state.TAG_KOA_ID, scenario.get_model_id(), is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Retrieve feature inference outputs and extract table.qza and asv
            scenario_proxy_fi = ScenarioProxy.from_existing_scenario(feature_scenario_id)
            protocol_proxy_fi = scenario_proxy_fi.get_protocol()
            feature_output = protocol_proxy_fi.get_process('feature_process').get_output('result_folder')

            # Get the table.qza and ASV-sequences.fasta from feature inference output
            feature_resource = protocol.add_process(InputTask, 'feature_resource', {InputTask.config_name: feature_output.get_model_id()})
            fs_node_extractor_table = protocol.add_process(FsNodeExtractor, 'fs_node_extractor_table', {"fs_node_path": "table.qza"})
            fs_node_extractor_asv = protocol.add_process(FsNodeExtractor, 'fs_node_extractor_asv', {"fs_node_path": "ASV-sequences.fasta"})
            # Add connectors
            protocol.add_connector(out_port=feature_resource >> 'resource', in_port=fs_node_extractor_table << "source")
            protocol.add_connector(out_port=feature_resource >> 'resource', in_port=fs_node_extractor_asv << "source")
            # Add 16S functional analysis process
            functional_analysis_process = protocol.add_process(KOA, 'functional_analysis_process',
                                                             config_params=gena_state.get_functional_analysis_config()["config"])

            # The task expects table.qza for ASV_count_abundance and ASV-sequences.fasta for FASTA_of_asv
            protocol.add_connector(out_port=fs_node_extractor_table >> "target", in_port=functional_analysis_process << 'ASV_count_abundance')
            protocol.add_connector(out_port=fs_node_extractor_asv >> "target", in_port=functional_analysis_process << 'FASTA_of_asv')

            # Add outputs
            protocol.add_output('functional_analysis_result_output', functional_analysis_process >> 'Folder_result', flag_resource=False)

            gena_state.reset_tree_analysis()
            gena_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

def render_koa_step(selected_scenario: Scenario, gena_state: State) -> None:
    # Get the selected tree menu item to determine which feature inference scenario is selected
    tree_menu = gena_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(gena_state.TAG_KOA):
        feature_scenario_parent_id = gena_state.get_parent_feature_inference_scenario_from_step()
        # save in session state
        gena_state.set_current_feature_scenario_id_parent(feature_scenario_parent_id.id)

    if not selected_scenario:
        if not gena_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of KOA analysis
            st.button("Run new KOA Analysis", icon=":material/play_arrow:", use_container_width=False,
                    on_click=lambda state=gena_state: dialog_koa_params(state))

        # Display table of existing KOA Analysis scenarios
        st.markdown("### Previous KOA Analysis")

        list_scenario_koa = gena_state.get_scenario_step_koa()
        render_scenario_table(list_scenario_koa, 'functional_analysis_process', 'koa_functional_grid', gena_state)
    else:
        # Display details about scenario KOA analysis
        st.markdown("##### KOA Analysis Scenario Results")
        display_scenario_parameters(selected_scenario, 'functional_analysis_process')

        if gena_state.get_is_standalone():
            return

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        # Get KOA analysis results folder
        koa_result_folder = protocol_proxy.get_process('koa_process').get_output('Folder_result')