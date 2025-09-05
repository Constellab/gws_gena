import streamlit as st
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core import ResourceSet, Scenario, ScenarioProxy, ProtocolProxy, InputTask, ProcessProxy, Scenario, ScenarioStatus, ScenarioProxy, ProtocolProxy
from gws_gena import ContextImporter
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import create_base_scenario_with_tags, search_updated_network

def render_context_step(selected_scenario: Scenario, gena_state: State) -> None:

    if not selected_scenario:
        # If a network has been saved, allow running Context Importer
        # Check if there's an updated network first
        file_network = search_updated_network(gena_state)
        if not file_network:
            st.info("Please save a network to proceed.")
            return

        if gena_state.get_is_standalone():
            return

        if st.button("Run context importer", icon=":material/play_arrow:", use_container_width=False):
            # Create a new scenario in the lab
            scenario = create_base_scenario_with_tags(gena_state, gena_state.TAG_CONTEXT, f"{gena_state.get_current_analysis_name()} - Quality check")
            protocol: ProtocolProxy = scenario.get_protocol()

            network_resource = protocol.add_process(
                InputTask, 'network_resource',
                {InputTask.config_name: gena_state.get_resource_id_network()})

            # Step 2 : Context task
            context_process : ProcessProxy = protocol.add_process(ContextImporter, 'context_process')
            protocol.add_connector(out_port=network_resource >> 'resource',
                                   in_port=context_process << 'source')
            # Add output
            protocol.add_output('context_process_output_folder', context_process >> 'target', flag_resource=False)
            scenario.add_to_queue()

            gena_state.reset_tree_analysis()
            gena_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

    else :
        # Visualize Context results
        st.markdown("##### Context Results")
        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

        # Retrieve outputs
        context_output : ResourceSet = protocol_proxy.get_process('context_process').get_output('target')


