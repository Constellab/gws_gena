import plotly.express as px
import streamlit as st
from gws_core import InputTask, Scenario, ScenarioProxy, ScenarioStatus
from gws_gena import FBA
from gws_streamlit_main import StreamlitTaskRunner

from ..functions_steps import (
    create_base_scenario_with_tags,
    display_network,
    display_saved_scenario_actions,
    display_scenario_parameters,
    extract_network_and_context_from_twin,
    render_scenario_table,
    should_include_row,
)
from ..state import State


@st.dialog("FBA parameters")
def dialog_fba_params(gena_state: State):
    translate_service = gena_state.get_translate_service()
    st.text_input(
        translate_service.translate("fba_scenario_name"),
        placeholder=translate_service.translate("enter_fba_name"),
        value=f"{gena_state.get_current_analysis_name()} - FBA",
        key=gena_state.FBA_SCENARIO_NAME_INPUT_KEY,
    )
    form_config = StreamlitTaskRunner(FBA)
    form_config.generate_config_form_without_run(
        session_state_key=gena_state.FBA_CONFIG_KEY,
        default_config_values=FBA.config_specs.get_default_values(),
        is_default_config_valid=FBA.config_specs.mandatory_values_are_set(
            FBA.config_specs.get_default_values()
        ),
    )

    # Add both Save and Run buttons
    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button(
            translate_service.translate("save_fba"),
            width="stretch",
            icon=":material/save:",
            key="button_fba_save",
        )

    with col2:
        run_clicked = st.button(
            translate_service.translate("run_fba"),
            width="stretch",
            icon=":material/play_arrow:",
            key="button_fba_run",
        )

    if save_clicked or run_clicked:
        if not gena_state.get_fba_config()["is_valid"]:
            st.warning(translate_service.translate("fill_mandatory_fields"))
            return

        scenario = create_base_scenario_with_tags(
            gena_state,
            gena_state.TAG_FBA,
            gena_state.get_scenario_user_name(gena_state.FBA_SCENARIO_NAME_INPUT_KEY),
        )
        twin_builder_id = gena_state.get_scenario_step_twin_builder()[0].id
        protocol = scenario.get_protocol()

        # Add fba process
        fba_process = protocol.add_process(
            FBA, "fba_process", config_params=gena_state.get_fba_config()["config"]
        )

        # Retrieve twin builder output and connect
        scenario_proxy_twin = ScenarioProxy.from_existing_scenario(twin_builder_id)
        protocol_proxy_twin = scenario_proxy_twin.get_protocol()
        twin_output = protocol_proxy_twin.get_process("twin_process").get_output("twin")

        twin_resource = protocol.add_process(
            InputTask, "twin_resource", {InputTask.config_name: twin_output.get_model_id()}
        )
        protocol.add_connector(out_port=twin_resource >> "resource", in_port=fba_process << "twin")

        # Add outputs
        protocol.add_output("fba_twin_output", fba_process >> "twin", flag_resource=False)
        protocol.add_output("fba_result_output", fba_process >> "fba_result", flag_resource=False)

        # Only add to queue if Run was clicked
        if run_clicked:
            scenario.add_to_queue()
            gena_state.reset_tree_analysis()
            gena_state.set_tree_default_item(scenario.get_model_id())

        st.rerun()


def render_fba_step(selected_scenario: Scenario, gena_state: State) -> None:
    translate_service = gena_state.get_translate_service()

    if not selected_scenario:
        if not gena_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of fba
            st.button(
                translate_service.translate("configure_new_fba"),
                icon=":material/edit:",
                width="stretch",
                on_click=lambda state=gena_state: dialog_fba_params(state),
            )

        # Display table of existing FBA scenarios
        st.markdown(f"### {translate_service.translate('list_scenarios')}")

        list_scenario_fba = gena_state.get_scenario_step_fba()
        render_scenario_table(list_scenario_fba, "fba_process", "fba_grid", gena_state)
    else:
        # Display details about scenario fba
        st.markdown(f"##### {translate_service.translate('fba_scenario_results')}")
        display_scenario_parameters(selected_scenario, "fba_process", gena_state)

        if selected_scenario.status == ScenarioStatus.DRAFT and not gena_state.get_is_standalone():
            display_saved_scenario_actions(selected_scenario, gena_state)

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()
        # Display fba table
        fba_result = (
            protocol_proxy.get_process("fba_process").get_output("fba_result").get_resources()
        )

        twin_resource_set_dict = (
            protocol_proxy.get_process("fba_process").get_output("twin").get_resources()
        )
        network_resource, context_resource = extract_network_and_context_from_twin(
            twin_resource_set_dict
        )

        tab_flux, tab_sv, tab_network, tab_context = st.tabs(
            [
                translate_service.translate("flux_table"),
                translate_service.translate("sv_table"),
                translate_service.translate("network"),
                translate_service.translate("context"),
            ]
        )
        with tab_flux:
            flux_data = fba_result.get("Flux table").get_data()

            # Check if index contains simulation suffixes
            simulation_numbers = set()

            for idx in flux_data.index:
                if isinstance(idx, str):
                    if "_simu" in idx:
                        parts = idx.split("_simu")
                        if len(parts) > 1 and parts[-1].isdigit():
                            simulation_numbers.add(int(parts[-1]))

            # If simulations are detected, add multiselect
            filtered_flux_data = flux_data
            if simulation_numbers:
                simulation_numbers = sorted(list(simulation_numbers))

                selected_simulations = st.multiselect(
                    translate_service.translate("select_simulations"),
                    options=simulation_numbers,
                    default=simulation_numbers,
                    key="flux_simulation_selector",
                )

                # Filter data based on selected simulations while maintaining order
                if selected_simulations:
                    mask = [
                        should_include_row(idx, selected_simulations) for idx in flux_data.index
                    ]
                    filtered_flux_data = flux_data.loc[mask]
                else:
                    st.info(translate_service.translate("no_simulation_selected"))
                    return

            st.dataframe(filtered_flux_data)

            # Create histogram of filtered flux values
            flux_values = filtered_flux_data.select_dtypes(include=["number"]).values.flatten()

            fig_flux = px.histogram(
                x=flux_values,
                title=translate_service.translate("flux_distribution"),
                labels={
                    "x": translate_service.translate("flux_values"),
                    "y": translate_service.translate("frequency"),
                },
            )
            st.plotly_chart(fig_flux, use_container_width=True)

        with tab_sv:
            sv_data = fba_result.get("SV table").get_data()

            # Check if index contains simulation suffixes
            simulation_numbers = set()

            for idx in sv_data.index:
                if isinstance(idx, str):
                    if "_simu" in idx:
                        parts = idx.split("_simu")
                        if len(parts) > 1 and parts[-1].isdigit():
                            simulation_numbers.add(int(parts[-1]))

            # If simulations are detected, add multiselect
            filtered_sv_data = sv_data
            if simulation_numbers:
                simulation_numbers = sorted(list(simulation_numbers))

                selected_simulations = st.multiselect(
                    translate_service.translate("select_simulations"),
                    options=simulation_numbers,
                    default=simulation_numbers,
                    key="sv_simulation_selector",
                )

                # Filter data based on selected simulations while maintaining order
                if selected_simulations:
                    mask = [should_include_row(idx, selected_simulations) for idx in sv_data.index]
                    filtered_sv_data = sv_data.loc[mask]
                else:
                    st.info(translate_service.translate("no_simulation_selected"))
                    return

            st.dataframe(filtered_sv_data)
            # Create distribution plot for SV values
            sv_values = filtered_sv_data.select_dtypes(include=["number"]).values.flatten()

            # Create histogram for distribution
            fig_sv_hist = px.histogram(
                x=sv_values,
                title=translate_service.translate("sv_distribution_histogram"),
                labels={
                    "x": translate_service.translate("sv_values"),
                    "y": translate_service.translate("frequency"),
                },
            )
            st.plotly_chart(fig_sv_hist, use_container_width=True)

        with tab_network:
            display_network(network_resource.get_model_id())
        with tab_context:
            st.json(context_resource.dumps())
