import os
import streamlit as st
import pandas as pd
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner, StreamlitResourceSelect
from gws_core import ResourceModel, FrontService, FsNodeExtractor, Scenario, ScenarioProxy, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_gena import KOA
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import extract_network_and_context_from_twin, display_network, create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("KOA parameters")
def dialog_koa_params(gena_state: State):
    st.text_input("KOA Analysis scenario name:", placeholder="Enter KOA analysis scenario name", value=f"{gena_state.get_current_analysis_name()} - KOA Analysis", key=gena_state.KOA_SCENARIO_NAME_INPUT_KEY)

    # select ko table data
    resource_select = StreamlitResourceSelect()
    resource_select.select_resource(
        placeholder='Search for ko table resource', key=gena_state.RESOURCE_SELECTOR_KO_TABLE_KEY, defaut_resource=None)

    form_config = StreamlitTaskRunner(KOA)
    form_config.generate_config_form_without_run(
        session_state_key=gena_state.KOA_CONFIG_KEY,
        default_config_values=KOA.config_specs.get_default_values(),
        is_default_config_valid=KOA.config_specs.mandatory_values_are_set(
            KOA.config_specs.get_default_values()))

    if st.button("Run KOA Analysis", use_container_width=True, icon=":material/play_arrow:", key="button_koa"):
        if not gena_state.get_koa_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            selected_ko_table_id = gena_state.get_resource_selector_ko_table()["resourceId"]
            selected_ko_table = ResourceModel.get_by_id(selected_ko_table_id)

            scenario = create_base_scenario_with_tags(gena_state, gena_state.TAG_KOA, gena_state.get_scenario_user_name(gena_state.KOA_SCENARIO_NAME_INPUT_KEY))
            protocol = scenario.get_protocol()

            ko_table_resource = protocol.add_process(
                InputTask, 'selected_ko_table',
                {InputTask.config_name: selected_ko_table.get_resource().get_model_id()})

            # Add KOA process
            koa_process = protocol.add_process(KOA, 'koa_process',
                                                  config_params=gena_state.get_koa_config()["config"])

            # Retrieve twin output and connect
            twin_builder_id = gena_state.get_scenario_step_twin_builder()[0].id
            scenario_proxy_fi = ScenarioProxy.from_existing_scenario(twin_builder_id)
            protocol_proxy_fi = scenario_proxy_fi.get_protocol()
            twin_output = protocol_proxy_fi.get_process('twin_process').get_output('twin')

            twin_resource = protocol.add_process(InputTask, 'twin_resource', {InputTask.config_name: twin_output.get_model_id()})
            protocol.add_connector(out_port=twin_resource >> 'resource', in_port=koa_process << 'twin')
            protocol.add_connector(out_port=ko_table_resource >> 'resource', in_port=koa_process << 'ko_table')

            # Add outputs
            protocol.add_output('koa_twin_output', koa_process >> 'twin', flag_resource=False)
            protocol.add_output('koa_result_output', koa_process >> 'koa_result', flag_resource=False)
            protocol.add_output('koa_table_summary_output', koa_process >> 'table_summary', flag_resource=False)


            scenario.add_to_queue()
            gena_state.reset_tree_analysis()
            gena_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

def render_koa_step(selected_scenario: Scenario, gena_state: State) -> None:

    if not selected_scenario:
        if not gena_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of KOA analysis
            st.button("Run new KOA Analysis", icon=":material/play_arrow:", use_container_width=False,
                    on_click=lambda state=gena_state: dialog_koa_params(state))

        # Display table of existing KOA Analysis scenarios
        st.markdown("### Previous KOA Analysis")

        list_scenario_koa = gena_state.get_scenario_step_koa()
        render_scenario_table(list_scenario_koa, 'koa_process', 'koa_grid', gena_state)
    else:
        # Display details about scenario KOA analysis
        st.markdown("##### KOA Analysis Scenario Results")
        display_scenario_parameters(selected_scenario, 'koa_process')

        if gena_state.get_is_standalone():
            return

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        # Get KOA analysis results folder
        koa_output = protocol_proxy.get_process('koa_process').get_output('koa_result')
        koa_table_summary = protocol_proxy.get_process('koa_process').get_output('table_summary')

        twin_resource_set_dict = protocol_proxy.get_process('koa_process').get_output('twin').get_resources()
        network_resource, context_resource = extract_network_and_context_from_twin(twin_resource_set_dict)

        tab_flux, tab_summary, tab_network, tab_context = st.tabs(["Flux tables", "Summary", "Network", "Context"])
        with tab_flux:
            # Display flux tables
            resource_set_result_dict = koa_output.get_resources()
            selected_result = st.selectbox("Select a flux table to display", options=resource_set_result_dict.keys(), key="flux_select")
            if selected_result:
                selected_resource = resource_set_result_dict.get(selected_result)
                st.dataframe(selected_resource.get_data())

        with tab_summary:
            st.dataframe(koa_table_summary.get_data())
        with tab_network:
            display_network(network_resource.get_model_id())
        with tab_context:
            st.json(context_resource.dumps())