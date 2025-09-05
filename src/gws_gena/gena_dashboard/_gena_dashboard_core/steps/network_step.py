import streamlit as st
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser
from gws_core import Scenario, ScenarioProxy, ProtocolProxy, File, TableImporter, Scenario, ScenarioProxy, ProtocolProxy
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import search_updated_network, save_network

def render_network_step(selected_scenario: Scenario, gena_state: State) -> None:
    # Check if there's an updated network first
    file_network = search_updated_network(gena_state)

    # If no updated network found, use the original scenario output
    if file_network is None:
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()
        file_network: File = protocol_proxy.get_process('network_importer_process').get_output('target')


    if not gena_state.get_scenario_step_qc():
        if not gena_state.get_is_standalone():
            st.markdown("### Edit network")


        else:
            st.markdown("### View network")
    else:
        st.markdown("### View network")

    # Save button only appear if Context task have not been created
    if not gena_state.get_scenario_step_context():
        if not gena_state.get_is_standalone():

            if st.button("Save", use_container_width=True):
                with StreamlitAuthenticateUser():
                    # Use the helper function to save
                    save_network(gena_state.get_edited_network(), gena_state)
                    st.rerun()
        else:
            st.info("ℹ️ You are in standalone mode. Network cannot be edited.")
    else:
        st.info("ℹ️ Network is locked because Context has already been run.")