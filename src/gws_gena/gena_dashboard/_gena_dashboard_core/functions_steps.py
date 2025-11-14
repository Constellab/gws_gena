from typing import List, Dict, Tuple
import streamlit as st
import pandas as pd
from streamlit_slickgrid import (
    slickgrid,
    FieldType,
    ExportServices,
)
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_gena import Network, Context
from gws_core import GenerateShareLinkDTO, ShareLinkEntityType, ShareLinkService, ResourceModel, Scenario, ScenarioProxy, File, SpaceFolder, Tag, Scenario, ScenarioStatus, ScenarioProxy, ScenarioCreationType, ScenarioSearchBuilder
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.tag import TagOrigin
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner

def get_status_emoji(status: ScenarioStatus) -> str:
    """Return appropriate emoji for scenario status"""
    emoji_map = {
        ScenarioStatus.DRAFT: "📝",
        ScenarioStatus.IN_QUEUE: "⏳",
        ScenarioStatus.WAITING_FOR_CLI_PROCESS: "⏸️",
        ScenarioStatus.RUNNING: "🔄",
        ScenarioStatus.SUCCESS: "✅",
        ScenarioStatus.ERROR: "❌",
        ScenarioStatus.PARTIALLY_RUN: "✔️"
    }
    return emoji_map.get(status, "")

def get_status_prettify(status: ScenarioStatus) -> str:
    """Return a human-readable string for scenario status"""
    prettify_map = {
        ScenarioStatus.DRAFT: "Draft",
        ScenarioStatus.IN_QUEUE: "In Queue",
        ScenarioStatus.WAITING_FOR_CLI_PROCESS: "Waiting",
        ScenarioStatus.RUNNING: "Running",
        ScenarioStatus.SUCCESS: "Success",
        ScenarioStatus.ERROR: "Error",
        ScenarioStatus.PARTIALLY_RUN: "Partially Run"
    }
    return prettify_map.get(status, "")

# Generic helper functions
def create_scenario_table_data(scenarios: List[Scenario], process_name: str) -> tuple:
    """Generic function to create table data from scenarios with their parameters."""
    table_data = []
    all_param_keys = set()
    scenarios_params = []

    # First pass: collect all parameter data and unique keys
    for scenario in scenarios:
        scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()
        process = protocol_proxy.get_process(process_name)
        config_params = process._process_model.config.to_simple_dto().values

        # For PCOA scenarios, add diversity table name from input resource
        if process_name == 'pcoa_process':
            config_params["Diversity Table"] = process.get_input('distance_table').name.split(" - ")[1]

        scenarios_params.append((scenario, config_params))
        all_param_keys.update(config_params.keys())

    # Second pass: create table data with all parameters
    for scenario, config_params in scenarios_params:
        row_data = {
            "id": scenario.id,
            "Scenario Name": scenario.title,
            "Creation Date": scenario.created_at.strftime("%Y-%m-%d %H:%M") if scenario.created_at else "",
            "Status": f"{get_status_emoji(scenario.status)} {get_status_prettify(scenario.status)}" if scenario.status else ""
        }

        # Add each parameter as a separate column
        for param_key in all_param_keys:
            row_data[param_key] = config_params.get(param_key, "")

        table_data.append(row_data)

    return table_data, all_param_keys

def create_slickgrid_columns(param_keys: set, gena_state : State) -> List[Dict]:
    """Generic function to create SlickGrid columns."""
    translate_service = gena_state.get_translate_service()
    columns = [
        {
            "id": "Scenario Name",
            "name": translate_service.translate("scenario_name"),
            "field": "Scenario Name",
            "sortable": True,
            "type": FieldType.string,
            "filterable": True,
            "width": 200,
        },
        {
            "id": "Creation Date",
            "name": translate_service.translate("creation_date"),
            "field": "Creation Date",
            "sortable": True,
            "type": FieldType.string,
            "filterable": True,
            "width": 100,
        },
        {
            "id": "Status",
            "name": translate_service.translate("status"),
            "field": "Status",
            "sortable": True,
            "type": FieldType.string,
            "filterable": True,
            "width": 60,
        },
    ]

    # Add parameter columns
    for param_key in sorted(param_keys):
        column_name = param_key.replace("_", " ").replace("-", " ").title()
        columns.append({
            "id": param_key,
            "name": column_name,
            "field": param_key,
            "sortable": True,
            "type": FieldType.string,
            "filterable": True,
            "width": 70,
        })

    return columns

def render_scenario_table(scenarios: List[Scenario], process_name: str, grid_key: str, gena_state: State) -> None:
    """Generic function to render a scenario table with parameters."""
    translate_service = gena_state.get_translate_service()
    if scenarios:
        table_data, all_param_keys = create_scenario_table_data(scenarios, process_name)
        columns = create_slickgrid_columns(all_param_keys, gena_state)

        options = {
            "enableFiltering": True,
            "enableTextExport": True,
            "enableExcelExport": True,
            "enableColumnPicker": True,
            "externalResources": [
                ExportServices.ExcelExportService,
                ExportServices.TextExportService,
            ],
            "autoResize": {
                "minHeight": 400,
            },
            "multiColumnSort": False,
        }

        out = slickgrid(table_data, columns=columns, options=options, key=grid_key, on_click="rerun")

        if out is not None:
            row_id, col = out
            selected_scenario = next((s for s in scenarios if s.id == row_id), None)
            if selected_scenario:
                gena_state.update_tree_menu_selection(selected_scenario.id)
                st.rerun()
    else:
        st.info(f"{translate_service.translate('no_analyses_found_prefix')} {process_name.replace('_', ' ').title()} {translate_service.translate('no_analyses_found')}")

def get_context_process_name(scenario: Scenario) -> str:
    """Get the process name used in a context scenario."""
    scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
    protocol_proxy = scenario_proxy.get_protocol()

    # Try context importer first
    try:
        if protocol_proxy.get_process('context_importer_process'):
            return 'context_importer_process'
    except:
        pass

    # Try context builder
    try:
        if protocol_proxy.get_process('context_builder_process'):
            return 'context_builder_process'
    except:
        pass

    # Default fallback
    return 'context_process'

def display_scenario_parameters(scenario: Scenario, process_name: str, gena_state : State) -> None:
    """Generic function to display scenario parameters in an expander."""
    translate_service = gena_state.get_translate_service()
    scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
    protocol_proxy = scenario_proxy.get_protocol()
    process = protocol_proxy.get_process(process_name)
    config_params = process._process_model.config.to_simple_dto().values

    # Add task name to parameters
    readable_task_name = process._process_model.name

    with st.expander(f"{translate_service.translate('parameters')} - {readable_task_name}"):
        param_data = []

        # Add task name as first parameter
        param_data.append({
            translate_service.translate("parameter"): "Task",
            translate_service.translate("value"): readable_task_name
        })

        for key, value in config_params.items():
            readable_key = key.replace("_", " ").replace("-", " ").title()
            param_data.append({
                translate_service.translate("parameter"): readable_key,
                translate_service.translate("value"): str(value)
            })

        if param_data:
            param_df = pd.DataFrame(param_data)
            st.dataframe(param_df, width="stretch", hide_index=True)

def create_base_scenario_with_tags(gena_state: State, step_tag: str, title: str) -> ScenarioProxy:
    """Generic function to create a scenario with base tags."""
    folder : SpaceFolder = SpaceFolder.get_by_id(gena_state.get_selected_folder_id())
    scenario: ScenarioProxy = ScenarioProxy(
        None, folder=folder,
        title=title,
        creation_type=ScenarioCreationType.MANUAL,
    )

    # Add base tags
    scenario.add_tag(Tag(gena_state.TAG_BRICK, gena_state.TAG_GENA, is_propagable=False, auto_parse=True))
    scenario.add_tag(Tag(gena_state.TAG_GENA, step_tag, is_propagable=False))
    scenario.add_tag(Tag(gena_state.TAG_ANALYSIS_NAME, gena_state.get_current_analysis_name(), is_propagable=False, auto_parse=True))
    scenario.add_tag(Tag(gena_state.TAG_GENA_PIPELINE_ID, gena_state.get_current_gena_pipeline_id(), is_propagable=False, auto_parse=True))

    return scenario

def add_tags_on_network(edited_network: Network, gena_state: State) -> None:
    """
    Helper function to add tags on network resource.
    """
    network_model_id = edited_network.get_model_id()

    # Add tags using EntityTagList
    user_origin = TagOrigin.current_user_origin()
    entity_tags = EntityTagList.find_by_entity(TagEntityType.RESOURCE, network_model_id)
    entity_tags._default_origin = user_origin # TODO will be fixed in future releases of core to set the default origin in the constructor

    # Add the required tags
    entity_tags.add_tag(Tag(gena_state.TAG_GENA, gena_state.TAG_NETWORK_UPDATED, is_propagable=False))
    entity_tags.add_tag(Tag(gena_state.TAG_GENA_PIPELINE_ID, gena_state.get_current_gena_pipeline_id(), is_propagable=False))

    gena_state.set_resource_id_network(network_model_id)

def search_updated_network(gena_state: State) -> File | None:
    """
    Helper function to search for updated network resource
    Returns the File resource if found, None otherwise
    """
    try:
        # Search for existing updated network resource
        pipeline_id_entities = EntityTag.select().where(
            (EntityTag.entity_type == TagEntityType.RESOURCE) &
            (EntityTag.tag_key == gena_state.TAG_GENA_PIPELINE_ID) &
            (EntityTag.tag_value == gena_state.get_current_gena_pipeline_id())
        )

        network_updated_entities = EntityTag.select().where(
            (EntityTag.entity_type == TagEntityType.RESOURCE) &
            (EntityTag.tag_key == gena_state.TAG_GENA) &
            (EntityTag.tag_value == gena_state.TAG_NETWORK_UPDATED)
        )

        pipeline_id_entity_ids = [entity.entity_id for entity in pipeline_id_entities]
        network_updated_entity_ids = [entity.entity_id for entity in network_updated_entities]
        common_entity_ids = list(set(pipeline_id_entity_ids) & set(network_updated_entity_ids))

        if common_entity_ids:
            network_resource_search = ResourceModel.select().where(
                (ResourceModel.id.in_(common_entity_ids)) &
                (ResourceModel.resource_typing_name.contains('Network'))
            )
            updated_resource = network_resource_search.first()

            if updated_resource:
                return updated_resource.get_resource()

    except Exception:
        pass

    return None


def display_network(network_model_id : str) -> None:
    # Generate a public share link for the network resource
    generate_link_dto = GenerateShareLinkDTO.get_1_hour_validity(
        entity_id=network_model_id,
        entity_type=ShareLinkEntityType.RESOURCE
    )

    share_link = ShareLinkService.get_or_create_valid_public_share_link(generate_link_dto)
    # Display html
    st.components.v1.iframe(share_link.get_public_link(), scrolling=True, height=500)

def extract_network_and_context_from_twin(twin_resource_set_dict : dict) -> Tuple[Network, Context]:
    # Navigate though the results and display them
    # If the typing is network, display the network
    # If the typing is context, display the json
    for key, value in twin_resource_set_dict.items():
        if value.get_typing_name() == "RESOURCE.gws_gena.Network":
            network_resource = twin_resource_set_dict.get(key)
        if value.get_typing_name() == "RESOURCE.gws_gena.Context":
            context_resource = twin_resource_set_dict.get(key)
    return network_resource, context_resource

def search_context(gena_state: State):
    """Retrieve context output from various possible processes."""
    selected_scenario = gena_state.get_scenario_step_context()
    if not selected_scenario:
        return None
    protocol_proxy = ScenarioProxy.from_existing_scenario(selected_scenario[0].id).get_protocol()

    # Try context importer first
    try:
        if protocol_proxy.get_process('context_importer_process'):
            return protocol_proxy.get_process('context_importer_process').get_output('target')
    except:
        pass

    # Try context builder
    try:
        if protocol_proxy.get_process('context_builder_process'):
            return protocol_proxy.get_process('context_builder_process').get_output('context')
    except:
        pass

    # Try selected context as input
    try:
        if protocol_proxy.get_process('selected_context'):
            return protocol_proxy.get_process('selected_context').get_output('resource')
    except:
        pass

    return None

def build_scenarios_by_step_dict(gena_pipeline_id: str, gena_state: State) -> Dict[str, List[Scenario]]:
    """
    Build scenarios_by_step dictionary for a given gena_pipeline_id.

    Args:
        gena_pipeline_id: The pipeline ID to search for scenarios
        gena_state: State object containing tag constants

    Returns:
        Dictionary mapping step names to lists of scenarios
    """
    gena_pipeline_id_parsed = Tag.parse_tag(gena_pipeline_id)

    # Get all scenarios for this analysis
    search_scenario_builder = ScenarioSearchBuilder() \
        .add_tag_filter(Tag(key=gena_state.TAG_GENA_PIPELINE_ID, value=gena_pipeline_id_parsed, auto_parse=True)) \
        .add_is_archived_filter(False)

    all_scenarios: List[Scenario] = search_scenario_builder.search_all()

    # Group scenarios by step type
    scenarios_by_step = {}
    for scenario in all_scenarios:
        entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id)
        tag_step_name = entity_tag_list.get_tags_by_key(gena_state.TAG_GENA)[0].to_simple_tag()
        step_name = tag_step_name.value

        if step_name not in scenarios_by_step:
            scenarios_by_step[step_name] = []
        scenarios_by_step[step_name].append(scenario)

    return scenarios_by_step

def display_saved_scenario_actions(scenario: Scenario, gena_state: State) -> None:
    """Display Run and Edit actions for saved scenarios."""
    translate_service = gena_state.get_translate_service()
    col1, col2 = st.columns(2)

    with col1:
        if st.button(translate_service.translate("run"), icon=":material/play_arrow:", key=f"run_{scenario.id}", width="stretch"):
            scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
            scenario_proxy.add_to_queue()
            gena_state.reset_tree_analysis()
            gena_state.set_tree_default_item(scenario.id)
            st.rerun()

    with col2:
        if st.button(translate_service.translate("edit"), icon=":material/edit:", key=f"edit_{scenario.id}", width="stretch"):
            dialog_edit_scenario_params(scenario, gena_state)

@st.dialog("Edit Scenario Parameters")
def dialog_edit_scenario_params(scenario: Scenario, gena_state: State):
    """Dialog to edit scenario parameters with Save and Run options."""
    translate_service = gena_state.get_translate_service()
    scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
    protocol_proxy = scenario_proxy.get_protocol()

    # Detect the process type based on scenario tags
    entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id)
    step_tag = entity_tag_list.get_tags_by_key(gena_state.TAG_GENA)[0].to_simple_tag().value

    # Map step tags to process names and task classes
    step_mapping = {
        gena_state.TAG_FBA: 'fba_process',
        gena_state.TAG_FVA: 'fva_process',
        gena_state.TAG_KOA: 'koa_process'
    }

    process_name, task_class = step_mapping[step_tag]
    task_class = None

    try:
        process = protocol_proxy.get_process(process_name)
        task_class = process.get_process_type()
        current_config = process._process_model.config.to_simple_dto().values
    except Exception as e:
        st.error(f"Could not retrieve process configuration: {str(e)}")
        return

    # Create a unique session state key for this edit dialog
    edit_config_key = f"edit_config_{scenario.id}"

    # Initialize the form with current configuration
    form_config = StreamlitTaskRunner(task_class)
    form_config.generate_config_form_without_run(
        session_state_key=edit_config_key,
        default_config_values=current_config,
        is_default_config_valid=True
    )

    # Add Save and Run buttons
    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button(translate_service.translate("save_changes"), icon=":material/save:", width="stretch", key=f"save_edit_{scenario.id}")

    with col2:
        run_clicked = st.button(translate_service.translate("save_and_run"), icon=":material/play_arrow:", width="stretch", key=f"run_edit_{scenario.id}")

    if save_clicked or run_clicked:
        # Get the updated configuration from session state
        updated_config = st.session_state.get(edit_config_key, {}).get("config", {})

        if not st.session_state.get(edit_config_key, {}).get("is_valid", False):
            st.warning(translate_service.translate("fill_mandatory_fields"))
            return

        with StreamlitAuthenticateUser():
            # Update the process configuration
            process.set_config_params(updated_config)

            if run_clicked:
                # If run is clicked, also add to queue
                scenario_proxy.add_to_queue()
                gena_state.reset_tree_analysis()
                gena_state.set_tree_default_item(scenario.id)

            # Clear the edit session state
            if edit_config_key in st.session_state:
                del st.session_state[edit_config_key]

            st.rerun()


# Create mask that preserves order
def should_include_row(idx, selected_simulations):
    """ Determine if a row should be included based on selected simulations.
    Used to filter flux data while maintaining order.
    In fba and fva steps"""
    if not isinstance(idx, str):
        return True

    # Handle numbered simulations
    parts = str(idx).split('_simu')
    if len(parts) > 1 and parts[-1].isdigit():
        return int(parts[-1]) in selected_simulations
    return True