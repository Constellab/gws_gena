import streamlit as st
from gws_core import Scenario, ScenarioSearchBuilder, Tag
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_entity_type import TagEntityType
from gws_streamlit_main import StreamlitContainers, StreamlitRouter
from streamlit_slickgrid import (
    ExportServices,
    FieldType,
    slickgrid,
)

from ..functions_steps import (
    build_scenarios_by_step_dict,
    delete_gena_recipe,
    get_status_emoji,
    rename_gena_recipe,
)
from ..state import State

# ---------------------------------------------------------------------------
# Session-state keys for the rename/delete dialogs
# ---------------------------------------------------------------------------
_GENA_DIALOG_STATE_KEY = "_gena_dialog_state"
_GENA_DIALOG_RECIPE_ID_KEY = "_gena_dialog_recipe_id"
_GENA_DIALOG_RECIPE_NAME_KEY = "_gena_dialog_recipe_name"
_GENA_DIALOG_ACTION_KEY = "_gena_dialog_action"


@st.dialog("Rename Recipe")
def _render_rename_dialog() -> None:
    """Modal dialog for renaming a gena recipe."""
    recipe_id: str = st.session_state[_GENA_DIALOG_RECIPE_ID_KEY]
    recipe_name: str = st.session_state.get(_GENA_DIALOG_RECIPE_NAME_KEY, "")
    gena_state: State = st.session_state[_GENA_DIALOG_STATE_KEY]
    translate_service = gena_state.get_translate_service()

    new_name = st.text_input(
        translate_service.translate("rename_recipe_label"),
        value=recipe_name,
    )

    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button(
            translate_service.translate("save"),
            type="primary",
            use_container_width=True,
        ):
            if not (new_name or "").strip():
                st.error(translate_service.translate("recipe_name_cannot_be_empty"))
            else:
                try:
                    rename_gena_recipe(recipe_id, (new_name or "").strip(), gena_state)
                    st.session_state[_GENA_DIALOG_ACTION_KEY] = None
                    st.session_state[_GENA_DIALOG_RECIPE_ID_KEY] = None
                    st.session_state["gena_recipes_refresh"] = (
                        st.session_state.get("gena_recipes_refresh", 0) + 1
                    )
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(
                        translate_service.translate("error_renaming_recipe").format(error=str(e))
                    )
    with col_cancel:
        if st.button(translate_service.translate("cancel"), use_container_width=True):
            st.session_state[_GENA_DIALOG_ACTION_KEY] = None
            st.session_state[_GENA_DIALOG_RECIPE_ID_KEY] = None
            st.rerun()


@st.dialog("Delete Recipe")
def _render_delete_dialog() -> None:
    """Modal dialog for confirming gena recipe deletion."""
    recipe_id: str = st.session_state[_GENA_DIALOG_RECIPE_ID_KEY]
    recipe_name: str = st.session_state.get(_GENA_DIALOG_RECIPE_NAME_KEY, "")
    gena_state: State = st.session_state[_GENA_DIALOG_STATE_KEY]
    translate_service = gena_state.get_translate_service()

    st.warning(translate_service.translate("confirm_delete_recipe").format(recipe_name=recipe_name))

    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button(
            translate_service.translate("confirm_delete"),
            type="primary",
            use_container_width=True,
        ):
            try:
                delete_gena_recipe(recipe_id, gena_state)
                st.session_state[_GENA_DIALOG_ACTION_KEY] = None
                st.session_state[_GENA_DIALOG_RECIPE_ID_KEY] = None
                st.session_state["gena_recipes_refresh"] = (
                    st.session_state.get("gena_recipes_refresh", 0) + 1
                )
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(translate_service.translate("error_deleting_recipe").format(error=str(e)))
    with col_cancel:
        if st.button(translate_service.translate("cancel"), use_container_width=True):
            st.session_state[_GENA_DIALOG_ACTION_KEY] = None
            st.session_state[_GENA_DIALOG_RECIPE_ID_KEY] = None
            st.rerun()


def render_first_page(gena_state: State):
    style = """
    [CLASS_NAME] {
        padding: 40px;
    }
    """

    with StreamlitContainers.container_full_min_height(
        "container-center_first_page", additional_style=style
    ):
        translate_service = gena_state.get_translate_service()

        # Add a button create new analysis using config
        # Create a container for the header with project title and action buttons
        col_title, col_button_new = StreamlitContainers.columns_with_fit_content(
            key="button_new", cols=[1, "fit-content"], vertical_align_items="center"
        )

        with col_title:
            st.markdown(f"## {translate_service.translate('retrieve_recipes')}")

        with col_button_new:
            if not gena_state.get_is_standalone():
                if st.button(
                    translate_service.translate("create_new_recipe"),
                    icon=":material/add:",
                    width="stretch",
                    type="primary",
                ):
                    # On click, navigate to a hidden page 'run new recipe'
                    router = StreamlitRouter.load_from_session()
                    router.navigate("new-analysis")

        # Add the table to retrieve the previous analysis
        search_scenario_builder = (
            ScenarioSearchBuilder()
            .add_tag_filter(Tag(key=gena_state.TAG_BRICK, value=gena_state.TAG_GENA))
            .add_tag_filter(Tag(key=gena_state.TAG_GENA, value=gena_state.TAG_NETWORK))
            .add_is_archived_filter(False)
        )

        # We got here all the network scenarios
        list_scenario_user: list[Scenario] = search_scenario_builder.search_all()

        # Create data for SlickGrid table
        table_data = []
        for scenario in list_scenario_user:
            entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id)
            tag_analysis_name = entity_tag_list.get_tags_by_key(gena_state.TAG_ANALYSIS_NAME)[
                0
            ].to_simple_tag()
            # Initialize row data with basic info
            row_data = {
                "id": scenario.id,
                "Name given": tag_analysis_name.value,
                "Folder": scenario.folder.name if scenario.folder else "",
                "network": get_status_emoji(scenario.status),
                "_action_rename": "✏️",
                "_action_delete": "🗑️",
            }

            # Get pipeline ID to find all related scenarios
            pipeline_id_tags = entity_tag_list.get_tags_by_key(gena_state.TAG_GENA_PIPELINE_ID)
            if pipeline_id_tags:
                pipeline_id = pipeline_id_tags[0].to_simple_tag().value

                # Search for all scenarios with this pipeline ID
                pipeline_search_builder = (
                    ScenarioSearchBuilder()
                    .add_tag_filter(Tag(key=gena_state.TAG_GENA_PIPELINE_ID, value=pipeline_id))
                    .add_is_archived_filter(False)
                )

                pipeline_scenarios = pipeline_search_builder.search_all()

                # Check each step type and add status to row data
                step_types = [
                    (gena_state.TAG_CONTEXT, "context"),
                    (gena_state.TAG_TWIN_BUILDER, "twin_builder"),
                    (gena_state.TAG_FBA, "fba"),
                    (gena_state.TAG_FVA, "fva"),
                    (gena_state.TAG_KOA, "koa"),
                ]

                for tag_value, field_name in step_types:
                    step_scenarios = [
                        s
                        for s in pipeline_scenarios
                        if any(
                            tag.tag_key == gena_state.TAG_GENA and tag.tag_value == tag_value
                            for tag in EntityTagList.find_by_entity(
                                TagEntityType.SCENARIO, s.id
                            ).get_tags()
                        )
                    ]

                    if step_scenarios:
                        # Get the most recent scenario for this step
                        latest_scenario = max(step_scenarios, key=lambda x: x.created_at)
                        row_data[field_name] = get_status_emoji(latest_scenario.status)
                    else:
                        row_data[field_name] = ""
            else:
                # Initialize empty status for other steps when no pipeline ID
                step_fields = ["context", "twin_builder", "fba", "fva", "koa"]
                for field in step_fields:
                    row_data[field] = ""

            table_data.append(row_data)

        if table_data:
            columns = [
                {
                    "id": "Name given",
                    "name": translate_service.translate("recipe_name"),
                    "field": "Name given",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 100,
                },
                {
                    "id": "Folder",
                    "name": translate_service.translate("folder"),
                    "field": "Folder",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 60,
                },
                {
                    "id": "network",
                    "name": translate_service.translate("model"),
                    "field": "network",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 40,
                },
                {
                    "id": "context",
                    "name": translate_service.translate("contextualisation"),
                    "field": "context",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 80,
                },
                {
                    "id": "twin_builder",
                    "name": translate_service.translate("twin"),
                    "field": "twin_builder",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 80,
                },
                {
                    "id": "fba",
                    "name": translate_service.translate("fba"),
                    "field": "fba",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 60,
                },
                {
                    "id": "fva",
                    "name": translate_service.translate("fva"),
                    "field": "fva",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 60,
                },
                {
                    "id": "koa",
                    "name": translate_service.translate("koa"),
                    "field": "koa",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 60,
                },
                {
                    "id": "_action_rename",
                    "name": "✏️",
                    "field": "_action_rename",
                    "sortable": False,
                    "filterable": False,
                    "width": 36,
                    "resizable": False,
                },
                {
                    "id": "_action_delete",
                    "name": "🗑️",
                    "field": "_action_delete",
                    "sortable": False,
                    "filterable": False,
                    "width": 36,
                    "resizable": False,
                },
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

            refresh_count = st.session_state.get("gena_recipes_refresh", 0)
            out = slickgrid(
                table_data,
                columns=columns,
                options=options,
                key=f"analysis_grid_{refresh_count}",
                on_click="rerun",
            )

            # Build action-column index map for click detection
            action_col_ids = {"_action_rename", "_action_delete"}
            action_col_by_idx = {
                i: col_def["id"]
                for i, col_def in enumerate(columns)
                if col_def["id"] in action_col_ids
            }

            if out is not None:
                row_id, col = out
                clicked_action = action_col_by_idx.get(col)

                if clicked_action and not gena_state.get_is_standalone():
                    # Action icon clicked — open rename/delete dialog
                    action = "rename" if clicked_action == "_action_rename" else "delete"
                    action_row = next((r for r in table_data if r["id"] == row_id), None)
                    st.session_state[_GENA_DIALOG_RECIPE_ID_KEY] = row_id
                    st.session_state[_GENA_DIALOG_ACTION_KEY] = action
                    st.session_state[_GENA_DIALOG_RECIPE_NAME_KEY] = (
                        action_row["Name given"] if action_row else ""
                    )
                    st.session_state[_GENA_DIALOG_STATE_KEY] = gena_state
                    st.rerun()
                else:
                    if col != 0 and col != 1:  # columns not related to a step
                        dict_id = next(
                            (entry for entry in table_data if entry["id"] == row_id), None
                        )
                        n = 0
                        for key, value in dict_id.items():
                            if n == col + 1:  # first column is the id (not displayed)
                                if value != "" and key not in action_col_ids:
                                    selected_scenario = next(
                                        (s for s in list_scenario_user if s.id == row_id), None
                                    )
                                    gena_state.set_selected_analysis(selected_scenario)
                                    entity_tag_list = EntityTagList.find_by_entity(
                                        TagEntityType.SCENARIO, selected_scenario.id
                                    )
                                    tag_gena_pipeline_id = entity_tag_list.get_tags_by_key(
                                        gena_state.TAG_GENA_PIPELINE_ID
                                    )[0].to_simple_tag()
                                    gena_pipeline_id = tag_gena_pipeline_id.value
                                    scenarios_by_step = build_scenarios_by_step_dict(
                                        gena_pipeline_id, gena_state
                                    )
                                    gena_state.set_scenarios_by_step_dict(scenarios_by_step)
                                    list_scenario = gena_state.get_scenarios_by_step_dict().get(key)
                                    latest_scenario = max(list_scenario, key=lambda x: x.created_at)
                                    gena_state.set_tree_default_item(latest_scenario.id)
                                    router = StreamlitRouter.load_from_session()
                                    router.navigate("analysis")
                                break
                            n += 1

                    # Handle row click
                    selected_scenario = next(
                        (s for s in list_scenario_user if s.id == row_id), None
                    )
                    if selected_scenario:
                        gena_state.set_selected_analysis(selected_scenario)
                        router = StreamlitRouter.load_from_session()
                        router.navigate("analysis")

            # Open the appropriate dialog when an action icon was clicked
            if (
                st.session_state.get(_GENA_DIALOG_ACTION_KEY)
                and st.session_state.get(_GENA_DIALOG_RECIPE_ID_KEY)
                and not gena_state.get_is_standalone()
            ):
                if st.session_state[_GENA_DIALOG_ACTION_KEY] == "rename":
                    _render_rename_dialog()
                elif st.session_state[_GENA_DIALOG_ACTION_KEY] == "delete":
                    _render_delete_dialog()

        else:
            st.info(translate_service.translate("no_recipe_found"))
