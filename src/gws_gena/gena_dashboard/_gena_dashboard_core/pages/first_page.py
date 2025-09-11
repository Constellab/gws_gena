import streamlit as st
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from typing import List
from gws_core.streamlit import StreamlitContainers, StreamlitRouter
from gws_core import Tag, ScenarioSearchBuilder, Scenario
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.entity_tag_list import EntityTagList
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import get_status_emoji
from streamlit_slickgrid import (
    slickgrid,
    FieldType,
    ExportServices,
)

def render_first_page(gena_state : State):

    # Add a button create new analysis using config
    # Create a container for the header with project title and action buttons
    col_title, col_button_new = StreamlitContainers.columns_with_fit_content(
            key="button_new",
            cols=[1, 'fit-content'], vertical_align_items='center')

    with col_title:
        st.markdown("## Retrieve analysis")

    with col_button_new:
        if not gena_state.get_is_standalone():
            if st.button("Create new analysis", icon=":material/add:", use_container_width=False, type = "primary"):
                # On click, navigate to a hidden page 'run new analysis'
                router = StreamlitRouter.load_from_session()
                router.navigate("new-analysis")


    # Add the table to retrieve the previous analysis
    search_scenario_builder = ScenarioSearchBuilder() \
        .add_tag_filter(Tag(key=gena_state.TAG_BRICK, value=gena_state.TAG_GENA)) \
        .add_tag_filter(Tag(key=gena_state.TAG_GENA, value=gena_state.TAG_NETWORK)) \
        .add_is_archived_filter(False)

    # We got here all the network scenarios
    list_scenario_user: List[Scenario] = search_scenario_builder.search_all()

    # Create data for SlickGrid table
    table_data = []
    for scenario in list_scenario_user:
        entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id)
        tag_analysis_name = entity_tag_list.get_tags_by_key(gena_state.TAG_ANALYSIS_NAME)[0].to_simple_tag()
        # Initialize row data with basic info
        row_data = {
            "id": scenario.id,
            "Name given": tag_analysis_name.value,
            "Folder": scenario.folder.name if scenario.folder else "",
            "network": get_status_emoji(scenario.status)
        }

        # Get pipeline ID to find all related scenarios
        pipeline_id_tags = entity_tag_list.get_tags_by_key(gena_state.TAG_GENA_PIPELINE_ID)
        if pipeline_id_tags:
            pipeline_id = pipeline_id_tags[0].to_simple_tag().value

            # Search for all scenarios with this pipeline ID
            pipeline_search_builder = ScenarioSearchBuilder() \
                .add_tag_filter(Tag(key=gena_state.TAG_GENA_PIPELINE_ID, value=pipeline_id)) \
                .add_is_archived_filter(False)

            pipeline_scenarios = pipeline_search_builder.search_all()

            # Check each step type and add status to row data
            step_types = [
                (gena_state.TAG_CONTEXT, "context"),
                (gena_state.TAG_TWIN_BUILDER, "twin_builder"),
                (gena_state.TAG_FBA, "fba"),
                (gena_state.TAG_FVA, "fva"),
                (gena_state.TAG_KOA, "koa"),
                (gena_state.TAG_TWIN_REDUCER, "twin_reducer"),
            ]

            for tag_value, field_name in step_types:
                step_scenarios = [s for s in pipeline_scenarios if any(
                    tag.tag_key == gena_state.TAG_GENA and tag.tag_value == tag_value
                    for tag in EntityTagList.find_by_entity(TagEntityType.SCENARIO, s.id).get_tags()
                )]

                if step_scenarios:
                    # Get the most recent scenario for this step
                    latest_scenario = max(step_scenarios, key=lambda x: x.created_at)
                    row_data[field_name] = get_status_emoji(latest_scenario.status)
                else:
                    row_data[field_name] = ""
        else:
            # Initialize empty status for other steps when no pipeline ID
            step_fields = ["context", "twin_builder", "fba", "fva", "koa", "twin_reducer"]
            for field in step_fields:
                row_data[field] = ""

        table_data.append(row_data)

    if table_data:
        columns = [
            {
                "id": "Name given",
                "name": "Analysis name",
                "field": "Name given",
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
                "width": 120,
            },
            {
                "id": "Folder",
                "name": "Folder",
                "field": "Folder",
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
                "width": 100,
            },
            {
                "id": "network",
                "name": "Network",
                "field": "network",
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
                "width": 60,
            },
            {
                "id": "context",
                "name": "Context",
                "field": "context",
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
                "width": 40,
            },
            {
                "id": "twin_builder",
                "name": "Twin Builder",
                "field": "twin_builder",
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
                "width": 60,
            },
            {
                "id": "fba",
                "name": "FBA",
                "field": "fba",
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
                "width": 60,
            },
            {
                "id": "fva",
                "name": "FVA",
                "field": "fva",
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
                "width": 60,
            },
            {
                "id": "koa",
                "name": "KOA",
                "field": "koa",
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
                "width": 60,
            },
            {
                "id": "twin_reducer",
                "name": "Twin Reducer",
                "field": "twin_reducer",
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
                "width": 80,
            }
        ]

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

        out = slickgrid(table_data, columns=columns, options=options, key="analysis_grid", on_click="rerun")

        if out is not None:
            row_id, col = out
            # Handle row click
            selected_scenario = next((s for s in list_scenario_user if s.id == row_id), None)
            if selected_scenario:
                gena_state.set_selected_analysis(selected_scenario)
                router = StreamlitRouter.load_from_session()
                router.navigate("analysis")

    else:
        st.info("No analysis found. Please click on 'Create new analysis' to create one.")
