import streamlit as st
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import Task, Scenario, ScenarioProxy, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_gena import TwinBuilder
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("Twin builder parameters")
def dialog_twin_builder_params(task_twin_builder: Task, gena_state: State):
    st.text_input("Twin builder scenario name:", placeholder="Enter twin builder scenario name", value=f"{gena_state.get_current_analysis_name()} - Twin Builder", key=gena_state.FEATURE_SCENARIO_NAME_INPUT_KEY)
    form_config = StreamlitTaskRunner(task_twin_builder)
    form_config.generate_config_form_without_run(
        session_state_key=gena_state.TWIN_BUILDER_CONFIG_KEY,
        default_config_values=task_twin_builder.config_specs.get_default_values(),
        is_default_config_valid=task_twin_builder.config_specs.mandatory_values_are_set(
            task_twin_builder.config_specs.get_default_values()))

    if st.button("Run Twin Builder", use_container_width=True, icon=":material/play_arrow:", key="button_fei"):
        if not gena_state.get_twin_builder_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(gena_state, gena_state.TAG_TWIN_BUILDER, gena_state.get_scenario_user_name(gena_state.FEATURE_SCENARIO_NAME_INPUT_KEY))
            scenario.add_tag(Tag(gena_state.TAG_TWIN_BUILDER_ID, scenario.get_model_id(), is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add twin builder process
            twin_process = protocol.add_process(task_twin_builder, 'twin_process',
                                                        config_params=gena_state.get_twin_builder_config()["config"])

            # Retrieve qc output and connect
            scenario_qc_id = gena_state.get_scenario_step_qc()[0].id
            scenario_proxy_qc = ScenarioProxy.from_existing_scenario(scenario_qc_id)
            protocol_proxy_qc = scenario_proxy_qc.get_protocol()
            qc_output = protocol_proxy_qc.get_process('qc_process').get_output('result_folder')

            qc_resource = protocol.add_process(InputTask, 'qc_resource', {InputTask.config_name: qc_output.get_model_id()})
            protocol.add_connector(out_port=qc_resource >> 'resource', in_port=twin_process << 'quality_check_folder')

            # Add outputs
            protocol.add_output('twin_process_boxplot_output', twin_process >> 'boxplot', flag_resource=False)
            protocol.add_output('twin_process_stats_output', twin_process >> 'stats', flag_resource=False)
            protocol.add_output('twin_process_folder_output', twin_process >> 'result_folder', flag_resource=False)

            scenario.add_to_queue()
            gena_state.reset_tree_analysis()
            gena_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

def render_twin_builder_step(selected_scenario: Scenario, gena_state: State) -> None:
    if not selected_scenario:
        # The task to display depends of single-end or paired-end
        if gena_state.get_sequencing_type() == "paired-end":
            task_twin_builder = Qiime2FeatureTableExtractorPE
        else:
            task_twin_builder = Qiime2FeatureTableExtractorSE

        if not gena_state.get_is_standalone():

            # On click, open a dialog to allow the user to select params of twin builder
            st.button("Run new Twin Builder", icon=":material/play_arrow:", use_container_width=False,
                    on_click=lambda task=task_twin_builder, state=gena_state: dialog_twin_builder_params(task, state))

        # Display table of existing Twin Builder scenarios
        st.markdown("### Previous Twin Builder Analyses")

        list_scenario_fi = gena_state.get_scenario_step_twin_builder()
        render_scenario_table(list_scenario_fi, 'twin_process', 'twin_builder_grid', gena_state)
    else:
        # Display details about scenario twin builder
        st.markdown("##### Twin Builder Scenario Results")
        display_scenario_parameters(selected_scenario, 'twin_process')
        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        tab_boxplot, tab_table = st.tabs(["Boxplot", "Table"])

        with tab_table:
            # Display stats
            stats_output = protocol_proxy.get_process('twin_process').get_output('stats')
            if stats_output and hasattr(stats_output, 'get_data'):
                st.dataframe(stats_output.get_data())

        with tab_boxplot:
            # Display boxplot
            boxplot_output = protocol_proxy.get_process('twin_process').get_output('boxplot').get_figure()
            if boxplot_output:
                st.plotly_chart(boxplot_output)