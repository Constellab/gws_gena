import streamlit as st
from typing import List, Dict
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core import Tag, Settings, File, ScenarioSearchBuilder,  Scenario, ScenarioStatus, ScenarioProxy, ProtocolProxy
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import search_context, search_updated_network, get_status_emoji, get_status_prettify, build_scenarios_by_step_dict
from gws_core.streamlit import StreamlitContainers, StreamlitRouter, StreamlitTreeMenu, StreamlitTreeMenuItem
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.entity_tag_list import EntityTagList

#Steps functions
from gws_gena.gena_dashboard._gena_dashboard_core.steps.network_step import render_network_step
from gws_gena.gena_dashboard._gena_dashboard_core.steps.context_step import render_context_step
from gws_gena.gena_dashboard._gena_dashboard_core.steps.twin_builder_step import render_twin_builder_step
from gws_gena.gena_dashboard._gena_dashboard_core.steps.fba_step import render_fba_step
from gws_gena.gena_dashboard._gena_dashboard_core.steps.fva_step import render_fva_step
from gws_gena.gena_dashboard._gena_dashboard_core.steps.koa_step import render_koa_step
from gws_gena.gena_dashboard._gena_dashboard_core.steps.twin_reducer_step import render_twin_reducer_step


# Check if steps are completed (have successful scenarios)
def has_successful_scenario(step_name : str, scenarios_by_step: Dict):
    if step_name not in scenarios_by_step:
        return False
    return any(s.status == ScenarioStatus.SUCCESS for s in scenarios_by_step[step_name])

# Helper function to get icon - check_circle if step has been run for specific parent, otherwise original icon
def get_step_icon(step_name: str, scenarios_by_step: Dict, list_scenarios: List[Scenario] = None) -> str:
    """Get icon for step - check_circle if step has scenarios, empty otherwise."""
    if step_name not in scenarios_by_step:
        return ''
    if not list_scenarios:
        return ''
    return 'check_circle'

def build_analysis_tree_menu(gena_state: State, gena_pipeline_id: str):
    """Build the tree menu for analysis workflow steps"""
    translate_service = gena_state.get_translate_service()
    button_menu = StreamlitTreeMenu(key=gena_state.TREE_ANALYSIS_KEY)

    # Build scenarios_by_step dictionary using helper function
    scenarios_by_step = build_scenarios_by_step_dict(gena_pipeline_id, gena_state)
    gena_state.set_scenarios_by_step_dict(scenarios_by_step)

    # 1) Network
    scenario_network = None
    if gena_state.TAG_NETWORK in scenarios_by_step:
        # If a scenario exists, use the first scenario's ID
        scenario_network = gena_state.get_scenario_step_network()
        key_network = scenario_network[0].id
    else:
        key_network = gena_state.TAG_NETWORK

    # Show the default selected item if exist either show first step
    if gena_state.get_tree_default_item():
        key_default_item = gena_state.get_tree_default_item()
    else :
        key_default_item = key_network

    network_item = StreamlitTreeMenuItem(
        label=translate_service.translate("network"),
        key=key_network,
        material_icon=get_step_icon(gena_state.TAG_NETWORK, scenarios_by_step, scenario_network)
    )

    button_menu.add_item(network_item)

    # 2) CONTEXT - only if network is successful
    if has_successful_scenario(gena_state.TAG_NETWORK, scenarios_by_step) or gena_state.TAG_CONTEXT in scenarios_by_step:
        scenario_context = None
        if gena_state.TAG_CONTEXT in scenarios_by_step:
            scenario_context = gena_state.get_scenario_step_context()
            # Use the first CONTEXT scenario's ID
            key_context = scenario_context[0].id
        else:
            key_context = gena_state.TAG_CONTEXT
        context_item = StreamlitTreeMenuItem(
            label=translate_service.translate("context"),
            key=key_context,
            material_icon=get_step_icon(gena_state.TAG_CONTEXT, scenarios_by_step, scenario_context)
        )

        button_menu.add_item(context_item)

    # 3) Twin builder - only if CONTEXT is successful
    if has_successful_scenario(gena_state.TAG_CONTEXT, scenarios_by_step) or gena_state.TAG_TWIN_BUILDER in scenarios_by_step:
        scenario_twin_builder = None
        if gena_state.TAG_TWIN_BUILDER in scenarios_by_step:
            scenario_twin_builder = gena_state.get_scenario_step_twin_builder()
            # Use the first Twin Builder scenario's ID
            key_twin_builder = scenario_twin_builder[0].id
        else:
            key_twin_builder = gena_state.TAG_TWIN_BUILDER
        twin_builder_item = StreamlitTreeMenuItem(
            label=translate_service.translate("twin"),
            key=key_twin_builder,
            material_icon=get_step_icon(gena_state.TAG_TWIN_BUILDER, scenarios_by_step, scenario_twin_builder)
        )
        button_menu.add_item(twin_builder_item)

    if has_successful_scenario(gena_state.TAG_TWIN_BUILDER, scenarios_by_step):
        # 4) FBA step
        fba_scenarios = scenarios_by_step.get(gena_state.TAG_FBA, [])
        fba_item = StreamlitTreeMenuItem(
            label=translate_service.translate("fba"),
            key=f"{gena_state.TAG_FBA}",
            material_icon=get_step_icon(gena_state.TAG_FBA, scenarios_by_step, fba_scenarios)
        )
        for fba_scenario in fba_scenarios:
            fba_scenario_item = StreamlitTreeMenuItem(
                label=fba_scenario.get_short_name(),
                key=fba_scenario.id,
                material_icon='description'
            )
            fba_item.add_children([fba_scenario_item])
        button_menu.add_item(fba_item)

        # 4) FVA step
        fva_scenarios = scenarios_by_step.get(gena_state.TAG_FVA, [])
        fva_item = StreamlitTreeMenuItem(
            label=translate_service.translate("fva"),
            key=f"{gena_state.TAG_FVA}",
            material_icon=get_step_icon(gena_state.TAG_FVA, scenarios_by_step, fva_scenarios)
        )
        for fva_scenario in fva_scenarios:
            fva_scenario_item = StreamlitTreeMenuItem(
                label=fva_scenario.get_short_name(),
                key=fva_scenario.id,
                material_icon='description'
            )
            fva_item.add_children([fva_scenario_item])
        button_menu.add_item(fva_item)

        # 4) KOA step
        koa_scenarios = scenarios_by_step.get(gena_state.TAG_KOA, [])
        koa_item = StreamlitTreeMenuItem(
            label=translate_service.translate("koa"),
            key=f"{gena_state.TAG_KOA}",
            material_icon=get_step_icon(gena_state.TAG_KOA, scenarios_by_step, koa_scenarios)
        )
        for koa_scenario in koa_scenarios:
            koa_scenario_item = StreamlitTreeMenuItem(
                label=koa_scenario.get_short_name(),
                key=koa_scenario.id,
                material_icon='description'
            )
            koa_item.add_children([koa_scenario_item])
        button_menu.add_item(koa_item)

        # 4) Twin Reducer - only if Twin Builder is successful
        twin_reducer_scenarios = scenarios_by_step.get(gena_state.TAG_TWIN_REDUCER, [])
        twin_reducer_item = StreamlitTreeMenuItem(
            label=translate_service.translate("twin_reducer"),
            key=f"{gena_state.TAG_TWIN_REDUCER}",
            material_icon=get_step_icon(gena_state.TAG_TWIN_REDUCER, scenarios_by_step, twin_reducer_scenarios)
        )
        for twin_reducer_scenario in twin_reducer_scenarios:
            twin_reducer_scenario_item = StreamlitTreeMenuItem(
                label=twin_reducer_scenario.get_short_name(),
                key=twin_reducer_scenario.id,
                material_icon='description'
            )
            twin_reducer_item.add_children([twin_reducer_scenario_item])
        button_menu.add_item(twin_reducer_item)

    return button_menu, key_default_item

def render_analysis_page(gena_state : State):
    translate_service = gena_state.get_translate_service()
    router = StreamlitRouter.load_from_session()
    # Create two columns
    left_col, right_col = st.columns([1, 4])

    with left_col:
        # Button to go home
        if st.button(translate_service.translate("recipes"), use_container_width=True, icon=":material/home:", type="primary"):
            # Reset the state of selected tree default item
            gena_state.set_tree_default_item(None)
            router = StreamlitRouter.load_from_session()
            router.navigate("first-page")

    selected_analysis = gena_state.get_selected_analysis()
    if not selected_analysis:
        return st.error(translate_service.translate("no_analysis_selected"))

    # Get analysis name from scenario tag
    entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, selected_analysis.id)
    tag_analysis_name = entity_tag_list.get_tags_by_key(gena_state.TAG_ANALYSIS_NAME)[0].to_simple_tag()
    analysis_name = tag_analysis_name.value

    # Get gena pipeline id from scenario tag
    tag_gena_pipeline_id = entity_tag_list.get_tags_by_key(gena_state.TAG_GENA_PIPELINE_ID)[0].to_simple_tag()
    gena_pipeline_id = tag_gena_pipeline_id.value

    # Get folder from scenario folder
    gena_state.set_selected_folder_id(selected_analysis.folder.id if selected_analysis.folder else None)

    if selected_analysis.status != ScenarioStatus.SUCCESS:
        if selected_analysis.status in [ScenarioStatus.RUNNING, ScenarioStatus.DRAFT, ScenarioStatus.WAITING_FOR_CLI_PROCESS, ScenarioStatus.IN_QUEUE, ScenarioStatus.PARTIALLY_RUN]:
            message = translate_service.translate("analysis_still_running")
        else:
            message = translate_service.translate("analysis_not_completed")
        with right_col:
            st.info(message)
        return

    scenario_proxy = ScenarioProxy.from_existing_scenario(selected_analysis.id)
    # Retrieve the protocol
    protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

    # Retrieve outputs

    ##### Network
    network_updated = search_updated_network(gena_state)

    if network_updated:
        gena_state.set_resource_id_network(network_updated.get_model_id())
    else : # Get the table from initial scenario
        network_output : File = protocol_proxy.get_process('network_process_output').get_input('resource')
        gena_state.set_resource_id_network(network_output.get_model_id())

    # Left column - Analysis workflow tree
    with left_col:

        st.write(f"**{translate_service.translate('recipe')}:** {analysis_name}")

        # Build and render the analysis tree menu, and keep the key of the first element
        tree_menu, key_default_item = build_analysis_tree_menu(gena_state, gena_pipeline_id)

        tree_menu.set_default_selected_item(key_default_item)

        # Save in session_state the tree_menu
        gena_state.set_tree_menu_object(tree_menu)

        # Render the tree menu
        selected_item = tree_menu.render()

        if selected_item is not None:
            # Handle tree item selection
            item_key = selected_item.key

            # If it's a scenario ID, update the selected scenario
            selected_scenario_new = Scenario.get_by_id(item_key)

            if selected_scenario_new:
                gena_state.set_selected_scenario(selected_scenario_new)

                entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, selected_scenario_new.id)
                tag_step_name = entity_tag_list.get_tags_by_key(gena_state.TAG_GENA)[0].to_simple_tag()
                gena_state.set_step_pipeline(tag_step_name.value)

            else:
                gena_state.set_selected_scenario(None)
                gena_state.set_step_pipeline(item_key)

    # Right column - Analysis details
    with right_col:
        #### Context
        context_file = search_context(gena_state)
        if context_file:
            gena_state.set_resource_id_context(context_file.get_model_id())

        # Add vertical line to separate the two columns
        style = """
        [CLASS_NAME] {
            border-left: 2px solid #ccc;
            min-height: 100vh;
            padding-left: 20px !important;
        }
        """
        with StreamlitContainers.container_with_style('analysis-container', style):

            is_scenario = True if gena_state.get_selected_scenario() else False

            if is_scenario:
                selected_scenario : Scenario = gena_state.get_selected_scenario()

                # Write the status of the scenario at the top right
                col_title, col_status, col_refresh= StreamlitContainers.columns_with_fit_content(
                        key="container_status",
                        cols=[1, 'fit-content', 'fit-content'], vertical_align_items='center')
                with col_title:
                    st.markdown(f"#### {selected_scenario.get_short_name()}")
                with col_status:
                    status_emoji = get_status_emoji(selected_scenario.status)
                    st.markdown(f"#### **{translate_service.translate('status')}:** {status_emoji} {get_status_prettify(selected_scenario.status)}")
                    # Add a button to redirect to the scenario page
                    virtual_host = Settings.get_instance().get_virtual_host()
                    if Settings.get_instance().is_prod_mode():
                        lab_mode = "lab"
                    else:
                        lab_mode = "dev-lab"
                    if not gena_state.get_is_standalone():
                        st.link_button(translate_service.translate("view_scenario"), f"https://{lab_mode}.{virtual_host}/app/scenario/{selected_scenario.id}", icon=":material/open_in_new:")
                with col_refresh:
                    # If the scenario status is running or in queue, add a refresh button to refresh the page
                    if selected_scenario.status in [ScenarioStatus.RUNNING, ScenarioStatus.WAITING_FOR_CLI_PROCESS, ScenarioStatus.IN_QUEUE]:
                        if st.button(translate_service.translate("refresh"), icon=":material/refresh:", use_container_width=False):
                            gena_state.set_tree_default_item(selected_scenario.id)
                            st.rerun()

            else :
                selected_scenario = None

            if gena_state.get_step_pipeline() == gena_state.TAG_NETWORK:
                # Render network step
                render_network_step(selected_scenario, gena_state)
            elif gena_state.get_step_pipeline() == gena_state.TAG_CONTEXT:
                render_context_step(selected_scenario, gena_state)
            elif gena_state.get_step_pipeline() == gena_state.TAG_TWIN_BUILDER:
                render_twin_builder_step(selected_scenario, gena_state)
            elif gena_state.get_step_pipeline().startswith(gena_state.TAG_TWIN_REDUCER):
                render_twin_reducer_step(selected_scenario, gena_state)
            elif gena_state.get_step_pipeline().startswith(gena_state.TAG_FBA):
                render_fba_step(selected_scenario, gena_state)
            elif gena_state.get_step_pipeline().startswith(gena_state.TAG_FVA):
                render_fva_step(selected_scenario, gena_state)
            elif gena_state.get_step_pipeline().startswith(gena_state.TAG_KOA):
                render_koa_step(selected_scenario, gena_state)
