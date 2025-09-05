import os
from typing import List, Dict
import streamlit as st
import numpy as np
import pandas as pd
from streamlit_slickgrid import (
    slickgrid,
    FieldType,
    ExportServices,
)
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser
from gws_core import Settings, ResourceModel, ResourceOrigin, Scenario, ScenarioProxy, File, SpaceFolder, Tag, Scenario, ScenarioStatus, ScenarioProxy, ScenarioCreationType
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
    scenario.add_tag(Tag(gena_state.TAG_FASTQ, gena_state.get_current_fastq_name(), is_propagable=False, auto_parse=True))
    scenario.add_tag(Tag(gena_state.TAG_BRICK, gena_state.TAG_GENA, is_propagable=False, auto_parse=True))
    scenario.add_tag(Tag(gena_state.TAG_GENA, step_tag, is_propagable=False))
    scenario.add_tag(Tag(gena_state.TAG_ANALYSIS_NAME, gena_state.get_current_analysis_name(), is_propagable=False, auto_parse=True))
    scenario.add_tag(Tag(gena_state.TAG_GENA_PIPELINE_ID, gena_state.get_current_gena_pipeline_id(), is_propagable=False, auto_parse=True))

    return scenario

def save_network(edited_df: pd.DataFrame, header_lines: List[str], gena_state: State) -> None:
    """
    Helper function to save network to resource.
    """

    # Search for existing updated network resource
    existing_resource = search_updated_network(gena_state)

    # If there's an existing resource, delete it first
    if existing_resource:
        ResourceModel.get_by_id(existing_resource.get_model_id()).delete_instance()

    # Create a new file with the updated content
    path_temp = os.path.join(os.path.abspath(os.path.dirname(__file__)), Settings.make_temp_dir())
    full_path = os.path.join(path_temp, f"{gena_state.get_current_analysis_name()}_Network_updated.json")

    # Prepare content to save
    content_to_save = ""
    if header_lines:
        content_to_save = '\n'.join(header_lines) + '\n'
    content_to_save += edited_df.to_csv(index=False, sep='\t')

    # Write content to file
    with open(full_path, 'w') as f:
        f.write(content_to_save)

    # Create File resource and save it properly using save_from_resource
    network_file = File(full_path)

    # Use save_from_resource which properly handles fs_node creation
    resource_model = ResourceModel.save_from_resource(
        network_file,
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
                (ResourceModel.resource_typing_name.contains('File'))
            )
            updated_resource = network_resource_search.first()

            if updated_resource:
                return updated_resource.get_resource()

    except Exception:
        pass

    return None
