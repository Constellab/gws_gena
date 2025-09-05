import streamlit as st
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import Scenario, ScenarioProxy, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_gena import FBA
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("FBA parameters")
def dialog_fba_params(gena_state: State):
    st.text_input("FBA scenario name:", placeholder="Enter FBA scenario name", value=f"{gena_state.get_current_analysis_name()} - FBA", key=gena_state.FBA_SCENARIO_NAME_INPUT_KEY)
    form_config = StreamlitTaskRunner(FBA)
    form_config.generate_config_form_without_run(
        session_state_key=gena_state.FBA_CONFIG_KEY,
        default_config_values=FBA.config_specs.get_default_values(),
        is_default_config_valid=FBA.config_specs.mandatory_values_are_set(
            FBA.config_specs.get_default_values()))

    if st.button("Run FBA", use_container_width=True, icon=":material/play_arrow:", key="button_fba"):
        if not gena_state.get_fba_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(gena_state, gena_state.TAG_FBA, gena_state.get_scenario_user_name(gena_state.FBA_SCENARIO_NAME_INPUT_KEY))
            feature_scenario_id = gena_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(gena_state.TAG_TWIN_BUILDER_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add fba process
            fba_process = protocol.add_process(FBA, 'fba_process',
                                                     config_params=gena_state.get_fba_config()["config"])

            # Retrieve feature inference output and connect
            scenario_proxy_fi = ScenarioProxy.from_existing_scenario(feature_scenario_id)
            protocol_proxy_fi = scenario_proxy_fi.get_protocol()
            feature_output = protocol_proxy_fi.get_process('feature_process').get_output('result_folder')

            feature_resource = protocol.add_process(InputTask, 'feature_resource', {InputTask.config_name: feature_output.get_model_id()})
            protocol.add_connector(out_port=feature_resource >> 'resource', in_port=fba_process << 'feature_frequency_folder')

            # Add outputs
            protocol.add_output('fba_table_output', fba_process >> 'fba_table', flag_resource=False)
            protocol.add_output('fba_folder_output', fba_process >> 'result_folder', flag_resource=False)

            scenario.add_to_queue()
            gena_state.reset_tree_analysis()
            gena_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

def render_fba_step(selected_scenario: Scenario, gena_state: State) -> None:
    # Get the selected tree menu item to determine which feature inference scenario is selected
    tree_menu = gena_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(gena_state.TAG_RAREFACTION):
        feature_scenario_parent_id = gena_state.get_parent_feature_inference_scenario_from_step()
        # save in session state
        gena_state.set_current_feature_scenario_id_parent(feature_scenario_parent_id.id)

    if not selected_scenario:
        if not gena_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of fba
            st.button("Run new FBA", icon=":material/play_arrow:", use_container_width=False,
                        on_click=lambda state=gena_state: dialog_fba_params(state))

        # Display table of existing FBA scenarios
        st.markdown("### Previous FBA Analyses")

        list_scenario_fba = gena_state.get_scenario_step_fba()
        render_scenario_table(list_scenario_fba, 'fba_process', 'fba_grid', gena_state)
    else:
        # Display details about scenario fba
        st.markdown("##### FBA Scenario Results")
        display_scenario_parameters(selected_scenario, 'fba_process')

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()
        # Display fba table
        fba_resource = protocol_proxy.get_process('fba_process').get_output('fba_table')
