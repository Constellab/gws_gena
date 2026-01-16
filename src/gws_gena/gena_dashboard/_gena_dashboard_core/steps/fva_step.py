import pandas as pd
import plotly.express as px
import streamlit as st
from gws_core import InputTask, Scenario, ScenarioProxy, ScenarioStatus
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_gena import FVA
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import (
    create_base_scenario_with_tags,
    display_network,
    display_saved_scenario_actions,
    display_scenario_parameters,
    extract_network_and_context_from_twin,
    render_scenario_table,
    should_include_row,
)
from gws_gena.gena_dashboard._gena_dashboard_core.state import State


@st.dialog("FVA parameters")
def dialog_fva_params(gena_state: State):
    translate_service = gena_state.get_translate_service()
    st.text_input(translate_service.translate("fva_scenario_name"), placeholder=translate_service.translate("enter_fva_name"), value=f"{gena_state.get_current_analysis_name()} - FVA", key=gena_state.FVA_SCENARIO_NAME_INPUT_KEY)
    form_config = StreamlitTaskRunner(FVA)
    form_config.generate_config_form_without_run(
        session_state_key=gena_state.FVA_CONFIG_KEY,
        default_config_values=FVA.config_specs.get_default_values(),
        is_default_config_valid=FVA.config_specs.mandatory_values_are_set(
            FVA.config_specs.get_default_values()))

    # Add both Save and Run buttons
    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button(translate_service.translate("save_fva"), width="stretch", icon=":material/save:", key="button_fva_save")

    with col2:
        run_clicked = st.button(translate_service.translate("run_fva"), width="stretch", icon=":material/play_arrow:", key="button_fva_run")

    if save_clicked or run_clicked:
        if not gena_state.get_fva_config()["is_valid"]:
            st.warning(translate_service.translate("fill_mandatory_fields"))
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(gena_state, gena_state.TAG_FVA, gena_state.get_scenario_user_name(gena_state.FVA_SCENARIO_NAME_INPUT_KEY))
            protocol = scenario.get_protocol()

            # Add FVA process
            fva_process = protocol.add_process(FVA, 'fva_process',
                                                  config_params=gena_state.get_fva_config()["config"])

            # Retrieve twin output and connect
            twin_builder_id = gena_state.get_scenario_step_twin_builder()[0].id
            scenario_proxy_fi = ScenarioProxy.from_existing_scenario(twin_builder_id)
            protocol_proxy_fi = scenario_proxy_fi.get_protocol()
            twin_output = protocol_proxy_fi.get_process('twin_process').get_output('twin')

            twin_resource = protocol.add_process(InputTask, 'twin_resource', {InputTask.config_name: twin_output.get_model_id()})
            protocol.add_connector(out_port=twin_resource >> 'resource', in_port=fva_process << 'twin')

            # Add outputs
            protocol.add_output('fva_twin_output', fva_process >> 'twin', flag_resource=False)
            protocol.add_output('fva_result_output', fva_process >> 'fva_result', flag_resource=False)

            # Only add to queue if Run was clicked
            if run_clicked:
                scenario.add_to_queue()
                gena_state.reset_tree_analysis()
                gena_state.set_tree_default_item(scenario.get_model_id())

            st.rerun()

def render_fva_step(selected_scenario: Scenario, gena_state: State) -> None:
    translate_service = gena_state.get_translate_service()

    if not selected_scenario:
        if not gena_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of fva
            st.button(translate_service.translate("configure_new_fva"), icon=":material/edit:", width="stretch",
                        on_click=lambda state=gena_state: dialog_fva_params(state))

        # Display table of existing FVA scenarios
        st.markdown(f"### {translate_service.translate('list_scenarios')}")

        list_scenario_fva = gena_state.get_scenario_step_fva()
        render_scenario_table(list_scenario_fva, 'fva_process', 'fva_grid', gena_state)
    else:
        # Display details about scenario fva
        st.markdown(f"##### {translate_service.translate('fva_scenario_results')}")
        display_scenario_parameters(selected_scenario, 'fva_process', gena_state)

        if selected_scenario.status == ScenarioStatus.DRAFT and not gena_state.get_is_standalone():
            display_saved_scenario_actions(selected_scenario, gena_state)

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        fva_result = protocol_proxy.get_process('fva_process').get_output('fva_result').get_resources()

        twin_resource_set_dict = protocol_proxy.get_process('fva_process').get_output('twin').get_resources()
        network_resource, context_resource = extract_network_and_context_from_twin(twin_resource_set_dict)

        tab_flux, tab_sv, tab_network, tab_context = st.tabs([translate_service.translate("flux_table"), translate_service.translate("sv_table"), translate_service.translate("network"), translate_service.translate("context")])

        with tab_flux:
            flux_data = fva_result.get("Flux table").get_data()

            # Check if index contains simulation suffixes
            simulation_numbers = set()

            for idx in flux_data.index:
                if isinstance(idx, str):
                    if '_simu' in idx:
                        parts = idx.split('_simu')
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
                    key="fva_flux_simulation_selector"
                )

                # Filter data based on selected simulations while maintaining order
                if selected_simulations:
                    mask = [should_include_row(idx, selected_simulations) for idx in flux_data.index]
                    filtered_flux_data = flux_data.loc[mask]
                else:
                    st.info(translate_service.translate("no_simulation_selected"))
                    return

            st.dataframe(filtered_flux_data)

            # Create histogram of filtered flux values
            flux_values = filtered_flux_data.select_dtypes(include=['number']).values.flatten()

            fig_flux = px.histogram(
                x=flux_values,
                title=translate_service.translate("flux_distribution"),
                labels={'x': translate_service.translate("flux_values"), 'y': translate_service.translate("frequency")}
            )
            st.plotly_chart(fig_flux, use_container_width=True)

            # Add flux range visualization with selection
            # Get reaction names (assuming first column or index contains reaction names)
            reaction_names = filtered_flux_data.index.tolist()

            # Multi-select for choosing reactions
            selected_reactions = st.multiselect(
                translate_service.translate("select_fluxes_to_display"),
                options=reaction_names,
                default=reaction_names[:min(10, len(reaction_names))]  # Default to first 10 reactions
            )

            if selected_reactions:
                # Filter data for selected reactions
                filtered_data = filtered_flux_data.loc[selected_reactions]
                flux_plot_data = []
                for reaction in selected_reactions:
                    row = filtered_data.loc[reaction]
                    flux_plot_data.append({
                        'Reaction': reaction,
                        'Value': row['value'],
                        'Lower_Bound': row['lower_bound'],
                        'Upper_Bound': row['upper_bound'],
                        'Range': row['upper_bound'] - row['lower_bound']
                    })

                plot_df = pd.DataFrame(flux_plot_data)

                # Create error bar plot
                fig_range = px.scatter(
                    plot_df,
                    x='Reaction',
                    y='Value',
                    error_y_minus=plot_df['Value'] - plot_df['Lower_Bound'],
                    error_y=plot_df['Upper_Bound'] - plot_df['Value'],
                    title=translate_service.translate("flux_range_plot_title"),
                    labels={'Reaction': translate_service.translate("reaction_names"), 'Value': translate_service.translate("flux_values")},
                    hover_data=['Lower_Bound', 'Upper_Bound', 'Range']
                )
                fig_range.update_traces(marker=dict(size=8))
                fig_range.update_xaxes(tickangle=45)
                st.plotly_chart(fig_range, use_container_width=True)

            else:
                st.info(translate_service.translate("select_flux_to_display"))

        with tab_sv:
            sv_data = fva_result.get("SV table").get_data()

            # Check if index contains simulation suffixes
            simulation_numbers = set()

            for idx in sv_data.index:
                if isinstance(idx, str):
                    if '_simu' in idx:
                        parts = idx.split('_simu')
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
                    key="fva_sv_simulation_selector"
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
            sv_values = filtered_sv_data.select_dtypes(include=['number']).values.flatten()

            # Create histogram for distribution
            fig_sv_hist = px.histogram(
                x=sv_values,
                title=translate_service.translate("sv_distribution_histogram"),
                labels={'x': translate_service.translate("sv_values"), 'y': translate_service.translate("frequency")}
            )
            st.plotly_chart(fig_sv_hist, use_container_width=True)

        with tab_network:
            display_network(network_resource.get_model_id())
        with tab_context:
            st.json(context_resource.dumps())
