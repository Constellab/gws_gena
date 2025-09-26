import streamlit as st
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner, StreamlitResourceSelect
from gws_core import ResourceModel, Scenario, ScenarioProxy, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_gena import KOA
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import display_saved_scenario_actions, extract_network_and_context_from_twin, display_network, create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("KOA parameters")
def dialog_koa_params(gena_state: State):
    translate_service = gena_state.get_translate_service()
    st.text_input(translate_service.translate("koa_analysis_scenario_name"), placeholder=translate_service.translate("enter_koa_name"), value=f"{gena_state.get_current_analysis_name()} - KOA Analysis", key=gena_state.KOA_SCENARIO_NAME_INPUT_KEY)

    # select ko table data
    resource_select = StreamlitResourceSelect()
    resource_select.select_resource(
        placeholder=translate_service.translate('search_ko_table'), key=gena_state.RESOURCE_SELECTOR_KO_TABLE_KEY, defaut_resource=None)

    form_config = StreamlitTaskRunner(KOA)
    form_config.generate_config_form_without_run(
        session_state_key=gena_state.KOA_CONFIG_KEY,
        default_config_values=KOA.config_specs.get_default_values(),
        is_default_config_valid=KOA.config_specs.mandatory_values_are_set(
            KOA.config_specs.get_default_values()))

    # Add both Save and Run buttons
    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button(translate_service.translate("save_koa"), use_container_width=True, icon=":material/save:", key="button_koa_save")

    with col2:
        run_clicked = st.button(translate_service.translate("run_koa"), use_container_width=True, icon=":material/play_arrow:", key="button_koa_run")

    if save_clicked or run_clicked:
        if not gena_state.get_koa_config()["is_valid"] or not gena_state.get_resource_selector_ko_table():
            st.warning(translate_service.translate("fill_mandatory_fields"))
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

            # Only add to queue if Run was clicked
            if run_clicked:
                scenario.add_to_queue()
                gena_state.reset_tree_analysis()
                gena_state.set_tree_default_item(scenario.get_model_id())

            st.rerun()

def render_koa_step(selected_scenario: Scenario, gena_state: State) -> None:
    translate_service = gena_state.get_translate_service()

    if not selected_scenario:
        if not gena_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of KOA analysis
            st.button(translate_service.translate("configure_new_koa"), icon=":material/edit:", use_container_width=False,
                    on_click=lambda state=gena_state: dialog_koa_params(state))

        # Display table of existing KOA Analysis scenarios
        st.markdown(f"### {translate_service.translate('list_scenarios')}")

        list_scenario_koa = gena_state.get_scenario_step_koa()
        render_scenario_table(list_scenario_koa, 'koa_process', 'koa_grid', gena_state)
    else:
        # Display details about scenario KOA analysis
        st.markdown(f"##### {translate_service.translate('koa_scenario_results')}")
        display_scenario_parameters(selected_scenario, 'koa_process', gena_state)

        if selected_scenario.status == ScenarioStatus.DRAFT and not gena_state.get_is_standalone():
            display_saved_scenario_actions(selected_scenario, gena_state)

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

        tab_flux, tab_summary, tab_network, tab_context = st.tabs([translate_service.translate("flux_tables"), translate_service.translate("summary"), translate_service.translate("network"), translate_service.translate("context")])
        with tab_flux:
            # Display flux tables
            resource_set_result_dict = koa_output.get_resources()
            selected_result = st.selectbox(translate_service.translate("select_flux_table"), options=resource_set_result_dict.keys(), key="flux_select")
            if selected_result:
                selected_resource = resource_set_result_dict.get(selected_result)
                st.dataframe(selected_resource.get_data())

        with tab_summary:
            st.dataframe(koa_table_summary.get_data())
        with tab_network:
            display_network(network_resource.get_model_id())
        with tab_context:
            st.json(context_resource.dumps())