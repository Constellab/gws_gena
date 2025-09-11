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
from gws_core import GenerateShareLinkDTO, ShareLinkEntityType, ShareLinkService, ResourceModel, ResourceOrigin, Scenario, ScenarioProxy, File, SpaceFolder, Tag, Scenario, ScenarioStatus, ScenarioProxy, ScenarioCreationType, ScenarioSearchBuilder
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.tag import TagOrigin

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

def create_slickgrid_columns(param_keys: set) -> List[Dict]:
    """Generic function to create SlickGrid columns."""
    columns = [
        {
            "id": "Scenario Name",
            "name": "Scenario Name",
            "field": "Scenario Name",
            "sortable": True,
            "type": FieldType.string,
            "filterable": True,
            "width": 200,
        },
        {
            "id": "Creation Date",
            "name": "Creation Date",
            "field": "Creation Date",
            "sortable": True,
            "type": FieldType.string,
            "filterable": True,
            "width": 100,
        },
        {
            "id": "Status",
            "name": "Status",
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
    if scenarios:
        table_data, all_param_keys = create_scenario_table_data(scenarios, process_name)
        columns = create_slickgrid_columns(all_param_keys)

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
        st.info(f"No {process_name.replace('_', ' ').title()} analyses found.")

def display_scenario_parameters(scenario: Scenario, process_name: str) -> None:
    """Generic function to display scenario parameters in an expander."""
    scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
    protocol_proxy = scenario_proxy.get_protocol()
    process = protocol_proxy.get_process(process_name)
    config_params = process._process_model.config.to_simple_dto().values

    with st.expander("Parameters - Reminder"):
        param_data = []
        for key, value in config_params.items():
            readable_key = key.replace("_", " ").replace("-", " ").title()
            param_data.append({
                "Parameter": readable_key,
                "Value": str(value)
            })

        if param_data:
            param_df = pd.DataFrame(param_data)
            st.dataframe(param_df, use_container_width=True, hide_index=True)

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

def save_network(edited_network: Network, gena_state: State) -> None:
    """
    Helper function to save network to resource.
    """

    # Search for existing updated network resource
    existing_resource = search_updated_network(gena_state)

    # If there's an existing resource, delete it first
    if existing_resource:
        ResourceModel.get_by_id(existing_resource.get_model_id()).delete_instance()

    # Use save_from_resource which properly handles fs_node creation
    resource_model = ResourceModel.save_from_resource(
        edited_network,
        origin=ResourceOrigin.UPLOADED,
        flagged=True
    )

    # Add tags using EntityTagList
    user_origin = TagOrigin.current_user_origin()
    entity_tags = EntityTagList(TagEntityType.RESOURCE, resource_model.id, default_origin=user_origin)

    # Add the required tags
    entity_tags.add_tag(Tag(gena_state.TAG_GENA, gena_state.TAG_NETWORK_UPDATED, is_propagable=False))
    entity_tags.add_tag(Tag(gena_state.TAG_GENA_PIPELINE_ID, gena_state.get_current_gena_pipeline_id(), is_propagable=False))

    gena_state.set_resource_id_network(resource_model.id)


def search_updated_network(gena_state: State) -> File | None:
    """
    Helper function to search for updated network resource.
    Returns the File resource if found, None otherwise.
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