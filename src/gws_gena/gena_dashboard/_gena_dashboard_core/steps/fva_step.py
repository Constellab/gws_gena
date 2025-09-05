import streamlit as st
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import Scenario, ScenarioProxy, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_gena import FVA
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("FVA parameters")
def dialog_fva_params(gena_state: State):
    st.text_input("FVA scenario name:", placeholder="Enter fva scenario name", value=f"{gena_state.get_current_analysis_name()} - FVA", key=gena_state.FVA_SCENARIO_NAME_INPUT_KEY)
    form_config = StreamlitTaskRunner(FVA)
    form_config.generate_config_form_without_run(
        session_state_key=gena_state.FVA_CONFIG_KEY,
        default_config_values=FVA.config_specs.get_default_values(),
        is_default_config_valid=FVA.config_specs.mandatory_values_are_set(
            FVA.config_specs.get_default_values()))

    if st.button("Run FVA", use_container_width=True, icon=":material/play_arrow:", key="button_fva"):
        if not gena_state.get_fva_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(gena_state, gena_state.TAG_FVA, gena_state.get_scenario_user_name(gena_state.FVA_SCENARIO_NAME_INPUT_KEY))
            feature_scenario_id = gena_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(gena_state.TAG_TWIN_BUILDER_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(gena_state.TAG_FVA_ID, scenario.get_model_id(), is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add FVA process
            fva_process = protocol.add_process(FVA, 'fva_process',
                                                  config_params=gena_state.get_fva_config()["config"])

            # Retrieve feature inference output and connect
            scenario_proxy_fi = ScenarioProxy.from_existing_scenario(feature_scenario_id)
            protocol_proxy_fi = scenario_proxy_fi.get_protocol()
            feature_output = protocol_proxy_fi.get_process('feature_process').get_output('result_folder')

            feature_resource = protocol.add_process(InputTask, 'feature_resource', {InputTask.config_name: feature_output.get_model_id()})
            protocol.add_connector(out_port=feature_resource >> 'resource', in_port=fva_process << 'rarefaction_analysis_result_folder')

            # Add outputs
            protocol.add_output('fva_tables_output', fva_process >> 'diversity_tables', flag_resource=False)
            protocol.add_output('fva_tables_output', fva_process >> 'fva_tables', flag_resource=False)
            protocol.add_output('fva_folder_output', fva_process >> 'result_folder', flag_resource=False)


            scenario.add_to_queue()
            gena_state.reset_tree_analysis()
            gena_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

def render_fva_step(selected_scenario: Scenario, gena_state: State) -> None:
    # Get the selected tree menu item to determine which feature inference scenario is selected
    tree_menu = gena_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(gena_state.TAG_FVA):
        feature_scenario_parent_id = gena_state.get_parent_feature_inference_scenario_from_step()
        # save in session state
        gena_state.set_current_feature_scenario_id_parent(feature_scenario_parent_id.id)

    if not selected_scenario:
        if not gena_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of fva
            st.button("Run new FVA", icon=":material/play_arrow:", use_container_width=False,
                        on_click=lambda state=gena_state: dialog_fva_params(state))

        # Display table of existing FVA scenarios
        st.markdown("### Previous FVA Analyses")

        list_scenario_fva = gena_state.get_scenario_step_fva()
        render_scenario_table(list_scenario_fva, 'fva_process', 'fva_grid', gena_state)
    else:
        # Display details about scenario fva
        st.markdown("##### FVA Scenario Results")
        display_scenario_parameters(selected_scenario, 'fva_process')

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        tab_diversity, tab_fva = st.tabs(["Diversity Tables", "FVA Tables"])

        with tab_diversity:
            # Display diversity tables
            diversity_resource_set = protocol_proxy.get_process('fva_process').get_output('diversity_tables')
            if diversity_resource_set:
                resource_set_result_dict = diversity_resource_set.get_resources()
                selected_result = st.selectbox("Select a diversity table to display", options=resource_set_result_dict.keys(), key="diversity_select")
                if selected_result:
                    selected_resource = resource_set_result_dict.get(selected_result)
                    if selected_resource.get_typing_name() == "RESOURCE.gws_core.Table":
                        st.dataframe(selected_resource.get_data())
                    elif selected_resource.get_typing_name() == "RESOURCE.gws_core.PlotlyResource":
                        st.plotly_chart(selected_resource.get_figure())

        with tab_fva:
            # Display fva tables
            fva_resource_set = protocol_proxy.get_process('fva_process').get_output('fva_tables')
            if fva_resource_set:
                resource_set_result_dict = fva_resource_set.get_resources()
                selected_result = st.selectbox("Select a result to display", options=resource_set_result_dict.keys(), key="fva_select")
                if selected_result:
                    selected_resource = resource_set_result_dict.get(selected_result)
                    if selected_resource.get_typing_name() == "RESOURCE.gws_core.Table":
                        st.dataframe(selected_resource.get_data())
                    elif selected_resource.get_typing_name() == "RESOURCE.gws_core.PlotlyResource":
                        st.plotly_chart(selected_resource.get_figure())