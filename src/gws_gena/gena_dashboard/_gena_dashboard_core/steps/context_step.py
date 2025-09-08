import os
import json
import streamlit as st
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core import ResourceOrigin, File, Settings, ResourceSet, Scenario, ScenarioProxy, ProtocolProxy, InputTask, ProcessProxy, ResourceModel, Scenario, ScenarioStatus, ScenarioProxy, ProtocolProxy
from gws_gena import ContextImporter, ContextBuilder
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import create_base_scenario_with_tags, search_updated_network
from gws_core.streamlit import StreamlitResourceSelect, StreamlitTaskRunner

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

        st.selectbox("Would you like to add a context?", options=["Yes", "No"], index=None, key=gena_state.CONTEXT_BOOL_KEY)
        if gena_state.get_context_bool() == "No":
            st.info("You can directly run context importer. Context will be empty.")
        elif gena_state.get_context_bool() == "Yes":
            st.selectbox("How would you like to provide context data?", options=["Select existing context resource", "Build a new context"], index=None, key=gena_state.CONTEXT_OPTION_KEY)
            if gena_state.get_context_option() == "Select existing context resource":
                # select context data
                resource_select = StreamlitResourceSelect()
                resource_select.select_resource(
                    placeholder='Search for context resource', key=gena_state.RESOURCE_SELECTOR_CONTEXT_KEY, defaut_resource=None)

            elif gena_state.get_context_option() == "Build a new context":
                st.info("In order to contextualise the network, you must select either a phenotype or a flux table.")
                # The user can select a phenotype table and/or a flux table to build a context
                # select phenotype table
                resource_select_phenotype = StreamlitResourceSelect()
                resource_select_phenotype.select_resource(
                    placeholder='Search for phenotype table resource', key=gena_state.RESOURCE_SELECTOR_PHENOTYPE_KEY, defaut_resource=None)

                # select flux table
                resource_select_flux = StreamlitResourceSelect()
                resource_select_flux.select_resource(
                    placeholder='Search for flux table resource', key=gena_state.RESOURCE_SELECTOR_FLUX_KEY, defaut_resource=None)
            else:
                st.info("Please select an option.")
                return
        else:
            st.info("Please select an option.")
            return
        if st.button("Run context importer", icon=":material/play_arrow:", use_container_width=False):
            if gena_state.get_context_bool() == "No":
                # Get the empty context and create a resource
                # Create a new file with the updated content
                path_temp = os.path.join(os.path.abspath(os.path.dirname(__file__)), Settings.make_temp_dir())
                full_path = os.path.join(path_temp, f"{gena_state.get_current_analysis_name()}_empty_context.json")

                # Prepare content to save
                content_to_save = {
                    "name": "empty_context",
                    'measures': []
                }

                json_str = json.dumps(content_to_save, indent=4)
                # Write content to file
                with open(full_path, 'w') as f:
                    f.write(json_str)

                # Create File resource and save it properly using save_from_resource
                context_file = File(full_path)

                # Use save_from_resource
                selected_context = ResourceModel.save_from_resource(
                    context_file,
                    origin=ResourceOrigin.UPLOADED,
                    flagged=True
                )
                # Create a new scenario in the lab
                scenario = create_base_scenario_with_tags(gena_state, gena_state.TAG_CONTEXT, f"{gena_state.get_current_analysis_name()} - Context")
                protocol: ProtocolProxy = scenario.get_protocol()

            else:
                if not gena_state.get_resource_selector_phenotype() and not gena_state.get_resource_selector_flux() and not gena_state.get_resource_selector_context():
                    st.warning("Please select at least one resource.")
                    return

                # Create a new scenario in the lab
                scenario = create_base_scenario_with_tags(gena_state, gena_state.TAG_CONTEXT, f"{gena_state.get_current_analysis_name()} - Context")
                protocol: ProtocolProxy = scenario.get_protocol()

                if gena_state.get_context_option() == "Build a new context":
                    selected_phenotype = None
                    selected_flux = None
                    if gena_state.get_resource_selector_phenotype():
                        selected_phenotype_id = gena_state.get_resource_selector_phenotype()["resourceId"]
                        selected_phenotype = ResourceModel.get_by_id(selected_phenotype_id)
                    if gena_state.get_resource_selector_flux():
                        selected_flux_id = gena_state.get_resource_selector_flux()["resourceId"]
                        selected_flux = ResourceModel.get_by_id(selected_flux_id)

                    # Network resource
                    network_resource = protocol.add_process(InputTask, 'network_resource', {InputTask.config_name: gena_state.get_resource_id_network()})

                    # Context builder task
                    context_process : ProcessProxy = protocol.add_process(ContextBuilder, 'context_builder_process')

                    protocol.add_connector(out_port=network_resource >> 'resource',
                                           in_port=context_process << 'network')

                    if selected_phenotype:
                        phenotype_resource = protocol.add_process(
                            InputTask, 'phenotype_resource',
                            {InputTask.config_name: selected_phenotype.get_resource().get_model_id()})
                        protocol.add_connector(out_port=phenotype_resource >> 'resource',
                                               in_port=context_process << 'pheno_table')

                    if selected_flux:
                        flux_resource = protocol.add_process(
                            InputTask, 'flux_resource',
                            {InputTask.config_name: selected_flux.get_resource().get_model_id()})
                        protocol.add_connector(out_port=flux_resource >> 'resource',
                                               in_port=context_process << 'flux_table')

                    # Add output
                    protocol.add_output('context_process_output', context_process >> 'context', flag_resource=False)
                    scenario.add_to_queue()

                    gena_state.reset_tree_analysis()
                    gena_state.set_tree_default_item(scenario.get_model_id())
                    st.rerun()
                    return
                else:
                    selected_context_id = gena_state.get_resource_selector_context()["resourceId"]
                    selected_context = ResourceModel.get_by_id(selected_context_id)
                    if selected_context.resource_typing_name == 'RESOURCE.gws_gena.Context':
                        # We don't need to import the context, it's already a context
                        protocol.add_process(InputTask, 'selected_context', {InputTask.config_name: selected_context.get_resource().get_model_id()})
                        scenario.add_to_queue()
                        gena_state.reset_tree_analysis()
                        gena_state.set_tree_default_item(scenario.get_model_id())
                        st.rerun()
                        return

            context_resource = protocol.add_process(
                InputTask, 'selected_context',
                {InputTask.config_name: selected_context.get_resource().get_model_id()})

            # Step 2 : Context task
            context_process : ProcessProxy = protocol.add_process(ContextImporter, 'context_importer_process')
            protocol.add_connector(out_port=context_resource >> 'resource',
                                   in_port=context_process << 'source')
            # Add output
            protocol.add_output('context_process_output', context_process >> 'target', flag_resource=False)
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
        # Context importer
        try :
            if protocol_proxy.get_process('context_importer_process'):
                context_output : ResourceSet = protocol_proxy.get_process('context_importer_process').get_output('target')
        except:
            try:
                # Context builder
                if protocol_proxy.get_process('context_builder_process'):
                    context_output : ResourceSet = protocol_proxy.get_process('context_builder_process').get_output('context')
            except:
                # Context already selected as input
                if protocol_proxy.get_process('selected_context'):
                    context_output : ResourceSet = protocol_proxy.get_process('selected_context').get_output('resource')

        st.json(context_output.dumps())
