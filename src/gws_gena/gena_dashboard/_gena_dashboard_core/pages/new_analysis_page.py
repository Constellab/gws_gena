import streamlit as st
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitResourceSelect, StreamlitRouter, StreamlitTaskRunner, StreamlitAuthenticateUser, StreamlitContainers
from gws_core import ResourceModel, SpaceFolder, StringHelper, Tag, InputTask, SpaceService, ProcessProxy, ScenarioProxy, ProtocolProxy, ScenarioCreationType
from gws_gena import NetworkImporter, LoadBiGGModels
from gws_gena import ConvertXmlToJson

def _flatten_folders_recursive(folders, folder_dict, folder_display_names, prefix="-"):
    """Recursively flatten folder hierarchy for display"""
    for folder in folders:
        display_name = f"{prefix}{folder.name}"
        folder_dict[folder.id] = folder.name
        folder_display_names[display_name] = folder.id

        # Recursively process children with increased indentation
        if hasattr(folder, 'children') and folder.children:
            _flatten_folders_recursive(folder.children, folder_dict, folder_display_names, prefix + "------")

def render_new_analysis_page(gena_state : State):
    # Add a return button
    router = StreamlitRouter.load_from_session()

    if st.button("Return recipes", icon=":material/arrow_back:", use_container_width=False):
        router.navigate("first-page")

    st.markdown("## New recipe")
    url_doc_network = "https://constellab.community/bricks/gws_gena/latest/doc/technical-folder/resource/Network"

    col_question, col_help = StreamlitContainers.columns_with_fit_content('container-column_network', cols=[1, 'fit-content'],
        vertical_align_items='center')
    with col_question:
        st.selectbox("How would you like to provide network data?",
            options=["Select existing network resource", "Load from BiGG Models"],
            index=None,
            key=gena_state.NETWORK_OPTION_KEY
        )
    with col_help:
        st.link_button("**?**", url_doc_network)
    network_selected_is_network = False
    if gena_state.get_network_option() == "Load from BiGG Models":
        form_config = StreamlitTaskRunner(LoadBiGGModels)
        form_config.generate_config_form_without_run(
            session_state_key=gena_state.LOAD_BIGG_MODEL_CONFIG_KEY, default_config_values=LoadBiGGModels.config_specs.get_default_values())

    elif gena_state.get_network_option() == "Select existing network resource":
        # select network data : the user can select network resource, file json or file xml or file matlab
        resource_select = StreamlitResourceSelect()
        resource_select.select_resource(
            placeholder='Search for network resource', key=gena_state.RESOURCE_SELECTOR_NETWORK_KEY)
        if gena_state.get_resource_selector_network():
            selected_network_id = gena_state.get_resource_selector_network()["resourceId"]
            selected_network = ResourceModel.get_by_id(selected_network_id)

            if selected_network.resource_typing_name == 'RESOURCE.gws_gena.Network':
                network_selected_is_network = True
    else:
        st.info("Please select an option")
        return

    if not network_selected_is_network:
        form_config = StreamlitTaskRunner(NetworkImporter)
        form_config.generate_config_form_without_run(
            session_state_key=gena_state.NETWORK_IMPORTER_CONFIG_KEY, default_config_values=NetworkImporter.config_specs.get_default_values(), key = "config_network_importer")

    cols = st.columns(2)
    with cols[0]:
        st.text_input("Insert your recipe name", key = gena_state.ANALYSIS_NAME_USER)

    with cols[1]:
        space_service = SpaceService.get_instance()
        list_folders_in_lab = space_service.get_all_lab_root_folders().folders
        folder_dict = {}
        folder_display_names = {}

        # Flatten the folder hierarchy recursively
        _flatten_folders_recursive(list_folders_in_lab, folder_dict, folder_display_names)

        # Give the user the possibility to choose from all folders (including children)
        folder_to_associate_with = st.selectbox(
            "Select folder to associate with",
            options=list(folder_display_names.keys()),
            index=None
        )
        # Save in session state the id of the folder
        gena_state.set_selected_folder_id(folder_display_names.get(folder_to_associate_with))

    if st.button("Run", icon=":material/play_arrow:", use_container_width=False):
        with StreamlitAuthenticateUser():
            list_required_fields_filled = []
            list_required_fields_filled.append(gena_state.check_if_required_is_filled(gena_state.get_analysis_name_user()))
            if gena_state.get_network_option() == "Load from BiGG Models":
                list_required_fields_filled.append(gena_state.get_load_bigg_model_config()["is_valid"])
            else:
                list_required_fields_filled.append(gena_state.check_if_required_is_filled(gena_state.get_resource_selector_network()))
                if not network_selected_is_network:
                    list_required_fields_filled.append(gena_state.get_network_importer_config()["is_valid"])
            if gena_state.get_associate_scenario_with_folder():
                list_required_fields_filled.append(gena_state.check_if_required_is_filled(gena_state.get_selected_folder_id()))
            # Check if mandatory fields have been filled
            if False in list_required_fields_filled:
                st.warning("Please fill all the mandatory fields.")
                return

            analysis_name = gena_state.get_analysis_name_user()
            # Create a new scenario in the lab
            folder : SpaceFolder = SpaceFolder.get_by_id(gena_state.get_selected_folder_id())
            scenario: ScenarioProxy = ScenarioProxy(
                None, folder=folder, title=f"{analysis_name} - Network",
                creation_type=ScenarioCreationType.MANUAL,
            )
            protocol: ProtocolProxy = scenario.get_protocol()
            if gena_state.get_network_option() == "Load from BiGG Models":
                # Step 1 : Load BiGG Models task
                load_bigg_models_process : ProcessProxy = protocol.add_process(LoadBiGGModels, 'load_bigg_models_process', config_params=gena_state.get_load_bigg_model_config()["config"])
            else:
                selected_network_id = gena_state.get_resource_selector_network()["resourceId"]
                selected_network = ResourceModel.get_by_id(selected_network_id)
                network_resource = protocol.add_process(
                    InputTask, 'selected_network',
                    {InputTask.config_name: selected_network.get_resource().get_model_id()})

            # We parse value to ensure it is a valid tag format because auto parse is not longer availaible
            # for values in lab
            analysis_name_parsed = Tag.parse_tag(analysis_name)

            # Add tags to the scenario
            scenario.add_tag(Tag(gena_state.TAG_BRICK, gena_state.TAG_GENA, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(gena_state.TAG_GENA, gena_state.TAG_NETWORK, is_propagable=False))
            scenario.add_tag(Tag(gena_state.TAG_ANALYSIS_NAME, analysis_name_parsed, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(gena_state.TAG_GENA_PIPELINE_ID, StringHelper.generate_uuid(), is_propagable=False, auto_parse=True))

            # Step 1 : Network task
            if not network_selected_is_network:
                network_importer_process: ProcessProxy = protocol.add_process(NetworkImporter, 'network_importer_process', config_params=gena_state.get_network_importer_config()["config"])
                
                if gena_state.get_network_option() == "Load from BiGG Models":
                    # BiGG Models already provides JSON format, connect directly to NetworkImporter
                    protocol.add_connector(out_port=load_bigg_models_process >> 'output',
                                        in_port=network_importer_process << 'source')
                else:
                    # Handle existing resource selection
                    selected_network_id = gena_state.get_resource_selector_network()["resourceId"]
                    selected_network = ResourceModel.get_by_id(selected_network_id)

                    # Check if the file is XML or Matlab (needs conversion)
                    is_xml_or_matlab = (selected_network.resource_typing_name == 'RESOURCE.gws_core.File'
                                        and selected_network.get_resource().extension in ['xml', 'mat'])

                    if is_xml_or_matlab:
                        # Add conversion step for XML/Matlab files
                        convert_xml_process: ProcessProxy = protocol.add_process(ConvertXmlToJson, 'convert_xml_to_json_process')
                        protocol.add_connector(out_port=network_resource >> 'resource',
                                            in_port=convert_xml_process << 'input_file')
                        protocol.add_connector(out_port=convert_xml_process >> 'output_json_file',
                                            in_port=network_importer_process << 'source')
                    else:
                        # Direct import for JSON files
                        protocol.add_connector(out_port=network_resource >> 'resource',
                                            in_port=network_importer_process << 'source')

                # Add output
                protocol.add_output('network_process_output', network_importer_process >> 'target', flag_resource=False)
            else:
                protocol.add_output('network_process_output', network_resource >> 'resource', flag_resource=False)
            scenario.add_to_queue()


            router.navigate("first-page")
            st.rerun()