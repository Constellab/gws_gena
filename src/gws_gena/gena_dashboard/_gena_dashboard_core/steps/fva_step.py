import streamlit as st
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import Scenario, ScenarioProxy, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_gena import FVA
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import display_saved_scenario_actions, display_network, extract_network_and_context_from_twin, create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("FVA parameters")
def dialog_fva_params(gena_state: State):
    translate_service = gena_state.get_translate_service()
    st.text_input(translate_service.translate("fva_scenario_name"), placeholder=translate_service.translate("enter_fva_name"), value=f"{gena_state.get_current_analysis_name()} - FVA", key=gena_state.FVA_SCENARIO_NAME_INPUT_KEY)
    form_config = StreamlitTaskRunner(FVA)
    form_config.generate_config_form_without_run(
        session_state_key=gena_state.FVA_CONFIG_KEY,
        default_config_values=FVA.config_specs.get_default_values(),
        is_default_config_valid=FVA.config_specs.mandatory_values_are_set(
            FVA.config_specs.get_default_values()))

    # Add both Save and Run buttons
    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button(translate_service.translate("save_fva"), use_container_width=True, icon=":material/save:", key="button_fva_save")

    with col2:
        run_clicked = st.button(translate_service.translate("run_fva"), use_container_width=True, icon=":material/play_arrow:", key="button_fva_run")

    if save_clicked or run_clicked:
        if not gena_state.get_fva_config()["is_valid"]:
            st.warning(translate_service.translate("fill_mandatory_fields"))
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(gena_state, gena_state.TAG_FVA, gena_state.get_scenario_user_name(gena_state.FVA_SCENARIO_NAME_INPUT_KEY))
            protocol = scenario.get_protocol()

            # Add FVA process
            fva_process = protocol.add_process(FVA, 'fva_process',
                                                  config_params=gena_state.get_fva_config()["config"])

            # Retrieve twin output and connect
            twin_builder_id = gena_state.get_scenario_step_twin_builder()[0].id
            scenario_proxy_fi = ScenarioProxy.from_existing_scenario(twin_builder_id)
            protocol_proxy_fi = scenario_proxy_fi.get_protocol()
            twin_output = protocol_proxy_fi.get_process('twin_process').get_output('twin')

            twin_resource = protocol.add_process(InputTask, 'twin_resource', {InputTask.config_name: twin_output.get_model_id()})
            protocol.add_connector(out_port=twin_resource >> 'resource', in_port=fva_process << 'twin')

            # Add outputs
            protocol.add_output('fva_twin_output', fva_process >> 'twin', flag_resource=False)
            protocol.add_output('fva_result_output', fva_process >> 'fva_result', flag_resource=False)

            # Only add to queue if Run was clicked
            if run_clicked:
                scenario.add_to_queue()
                gena_state.reset_tree_analysis()
                gena_state.set_tree_default_item(scenario.get_model_id())

            st.rerun()

def render_fva_step(selected_scenario: Scenario, gena_state: State) -> None:
    translate_service = gena_state.get_translate_service()

    if not selected_scenario:
        if not gena_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of fva
            st.button(translate_service.translate("configure_new_fva"), icon=":material/edit:", use_container_width=False,
                        on_click=lambda state=gena_state: dialog_fva_params(state))

        # Display table of existing FVA scenarios
        st.markdown(f"### {translate_service.translate('list_scenarios')}")

        list_scenario_fva = gena_state.get_scenario_step_fva()
        render_scenario_table(list_scenario_fva, 'fva_process', 'fva_grid', gena_state)
    else:
        # Display details about scenario fva
        st.markdown(f"##### {translate_service.translate('fva_scenario_results')}")
        display_scenario_parameters(selected_scenario, 'fva_process', gena_state)

        if selected_scenario.status == ScenarioStatus.DRAFT and not gena_state.get_is_standalone():
            display_saved_scenario_actions(selected_scenario, gena_state)

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        fva_result = protocol_proxy.get_process('fva_process').get_output('fva_result').get_resources()

        twin_resource_set_dict = protocol_proxy.get_process('fva_process').get_output('twin').get_resources()
        network_resource, context_resource = extract_network_and_context_from_twin(twin_resource_set_dict)

        tab_flux, tab_sv, tab_network, tab_context = st.tabs([translate_service.translate("flux_table"), translate_service.translate("sv_table"), translate_service.translate("network"), translate_service.translate("context")])
        with tab_flux:
            st.dataframe(fva_result.get("Flux table").get_data())
        with tab_sv:
            st.dataframe(fva_result.get("SV table").get_data())
        with tab_network:
            display_network(network_resource.get_model_id())
        with tab_context:
            st.json(context_resource.dumps())
