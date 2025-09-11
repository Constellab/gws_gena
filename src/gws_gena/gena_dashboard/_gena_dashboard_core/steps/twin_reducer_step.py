import streamlit as st
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import Scenario, ScenarioProxy, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_gena import TwinReducer
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("Twin Reducer parameters")
def dialog_twin_reducer_params(gena_state: State):
    st.text_input("Twin Reducer scenario name:", placeholder="Enter Twin Reducer scenario name", value=f"{gena_state.get_current_analysis_name()} - Twin Reducer", key=gena_state.TWIN_REDUCER_SCENARIO_NAME_INPUT_KEY)
    form_config = StreamlitTaskRunner(TwinReducer)
    form_config.generate_config_form_without_run(
        session_state_key=gena_state.TWIN_REDUCER_CONFIG_KEY,
        default_config_values=TwinReducer.config_specs.get_default_values(),
        is_default_config_valid=TwinReducer.config_specs.mandatory_values_are_set(
            TwinReducer.config_specs.get_default_values()))

    if st.button("Run Twin Reducer", use_container_width=True, icon=":material/play_arrow:", key="button_twin_reducer"):
        if not gena_state.get_twin_reducer_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(gena_state, gena_state.TAG_TWIN_REDUCER, gena_state.get_scenario_user_name(gena_state.TWIN_REDUCER_SCENARIO_NAME_INPUT_KEY))
            twin_builder_id = gena_state.get_scenario_step_twin_builder()[0].id
            protocol = scenario.get_protocol()

            # Add twin reducer process
            twin_reducer_process = protocol.add_process(TwinReducer, 'twin_reducer_process',
                                                     config_params=gena_state.get_twin_reducer_config()["config"])

            # Retrieve twin builder output and connect
            scenario_proxy_twin = ScenarioProxy.from_existing_scenario(twin_builder_id)
            protocol_proxy_twin = scenario_proxy_twin.get_protocol()
            twin_output = protocol_proxy_twin.get_process('twin_process').get_output('twin')

            twin_resource = protocol.add_process(InputTask, 'twin_resource', {InputTask.config_name: twin_output.get_model_id()})
            protocol.add_connector(out_port=twin_resource >> 'resource', in_port=twin_reducer_process << 'twin')

            # Add outputs
            protocol.add_output('efm_table_output', twin_reducer_process >> 'efm_table', flag_resource=False)
            protocol.add_output('reduction_table_output', twin_reducer_process >> 'reduction_table', flag_resource=False)

            scenario.add_to_queue()
            gena_state.reset_tree_analysis()
            gena_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

def render_twin_reducer_step(selected_scenario: Scenario, gena_state: State) -> None:

    if not selected_scenario:
        if not gena_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of twin reducer
            st.button("Run new Twin Reducer", icon=":material/play_arrow:", use_container_width=False,
                        on_click=lambda state=gena_state: dialog_twin_reducer_params(state))

        # Display table of existing Twin Reducer scenarios
        st.markdown("### Previous Twin Reducer Analyses")

        list_scenario_twin_reducer = gena_state.get_scenario_step_twin_reducer()
        render_scenario_table(list_scenario_twin_reducer, 'twin_reducer_process', 'twin_reducer_grid', gena_state)
    else:
        # Display details about scenario twin reducer
        st.markdown("##### Twin Reducer Scenario Results")
        display_scenario_parameters(selected_scenario, 'twin_reducer_process')

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()
        # Display twin reducer tables
        efm_table = protocol_proxy.get_process('twin_reducer_process').get_output('efm_table')
        reduction_table = protocol_proxy.get_process('twin_reducer_process').get_output('reduction_table')

        tab_efm, tab_reduction = st.tabs(["EFM table", "Reduction table"])
        with tab_efm:
            st.dataframe(efm_table.get_data())
        with tab_reduction:
            st.dataframe(reduction_table.get_data())