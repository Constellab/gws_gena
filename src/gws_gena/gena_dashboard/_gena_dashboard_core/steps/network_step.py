import os
import streamlit as st
import pandas as pd
from typing import Type, Dict, Optional
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner, StreamlitMenuButton, StreamlitMenuButtonItem, StreamlitContainers, StreamlitResourceSelect
from gws_core import Settings, ScenarioStatus, Scenario, ResourceModel, ScenarioProxy, Scenario, ScenarioWaiterBasic, InputTask, File, TableImporter, ResourceOrigin
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import display_network, add_tags_on_network, get_status_prettify, get_status_emoji
from gws_gena import GapFiller, ReactionAdder, ReactionRemover, OrphanRemover, NetworkMerger, NetworkMergem, TransporterAdder
from gws_core.task.task import Task

def display_process_history(processes_list, gena_state : State):
    """Display a nice timeline view of all processes in the protocol"""
    translate_service = gena_state.get_translate_service()  # Get translate service

    st.markdown(f"### {translate_service.translate('process_history')}")

    # Create a DataFrame for better display
    history_data = []

    for i, process in enumerate(processes_list):
        # Get timing information
        started_at = process.started_at if hasattr(process, 'started_at') and process.started_at else None
        ended_at = process.ended_at if hasattr(process, 'ended_at') and process.ended_at else None

        # Calculate duration
        duration = ""
        if started_at and ended_at:
            duration_seconds = (ended_at - started_at).total_seconds()
            if duration_seconds < 60:
                duration = f"{duration_seconds:.1f}s"
            elif duration_seconds < 3600:
                duration = f"{duration_seconds/60:.1f}min"
            else:
                duration = f"{duration_seconds/3600:.1f}h"


        history_data.append({
            translate_service.translate('step'): i + 1,
            translate_service.translate('process_name'): process.name,
            translate_service.translate('started'): started_at.strftime("%Y-%m-%d %H:%M:%S") if started_at else translate_service.translate("not_started"),
            translate_service.translate('ended'): ended_at.strftime("%Y-%m-%d %H:%M:%S") if ended_at else translate_service.translate("not_finished"),
            translate_service.translate('duration'): duration
        })

    # Display timeline cards
    for i, data in enumerate(history_data):
        # Create a card-like container for each process
        with st.container():
            # Create columns
            col_step, col_info, col_timing = st.columns([1, 3, 3])

            with col_step:
                st.markdown(f"**#{data[translate_service.translate('step')]}**")

            with col_info:
                st.markdown(f"**{data[translate_service.translate('process_name')]}**")

            with col_timing:
                if data[translate_service.translate('started')] != translate_service.translate("not_started"):
                    st.markdown(f"**{translate_service.translate('started')}:** {data[translate_service.translate('started')]}")
                    if data[translate_service.translate('ended')] != translate_service.translate("not_finished"):
                        st.markdown(f"**{translate_service.translate('ended')}:** {data[translate_service.translate('ended')]}")
                        st.markdown(f"**{translate_service.translate('duration')}:** {data[translate_service.translate('duration')]}")
                    else:
                        st.markdown(f"**{translate_service.translate('still_running')}**")
                else:
                    st.markdown(f"**{translate_service.translate('not_started_yet')}**")

        # Add a separator between processes (except for the last one)
        if i < len(history_data) - 1:
            st.divider()


def _run_network_editing_task(
    task_class: Type[Task],
    task_name: str,
    gena_state: State,
    config_session_key: str,
    config_getter_method: str,
    task_input_name_for_network: str = 'network',
    additional_inputs: Optional[Dict[str, Dict[str, str]]] = None,
    table_type_options: Optional[Dict[str, list]] = None
) -> None:
    """
    Generic function to run network editing tasks.

    Args:
        task_class: The task class to run
        task_name: Display name for the task
        gena_state: Application state
        config_session_key: Session key for configuration
        config_getter_method: Method name to get configuration from state
        additional_inputs: Dictionary of additional input specifications
                          Format: {'input_port_name': {'session_key': 'key', 'placeholder': 'text'}}
        table_type_options: Dictionary mapping input ports to their table column options
                           Format: {'input_port_name': ['column1', 'column2']}
    """
    translate_service = gena_state.get_translate_service()
    # Handle additional resource inputs
    selected_resources = {}
    created_tables = {}
    if additional_inputs:
        # Selectbox to choose an existing resource or create a new one
        type_resource_selection = st.selectbox(
            label=translate_service.translate("please_select_option"),
            options=[translate_service.translate("select_resource"), translate_service.translate("create_new_resource")],
            index=0
        )

        if type_resource_selection == translate_service.translate("select_resource"):
            st.markdown(f"#### {translate_service.translate('select_additional_resources')}")

            for input_port, input_config in additional_inputs.items():
                resource_select = StreamlitResourceSelect()
                resource_select.select_resource(
                    placeholder=input_config['placeholder'],
                    key=input_config['session_key'],
                    defaut_resource=None
                )

                # Get the selected resource from session state
                selected_resource = getattr(gena_state, f"get_{input_config['session_key'].replace('_KEY', '').lower()}")()
                if selected_resource:
                    selected_resources[input_port] = selected_resource["resourceId"]

        elif type_resource_selection == translate_service.translate("create_new_resource"):
            with st.expander(translate_service.translate("create_new_resource"), icon=":material/edit_note:", expanded=True):

                for input_port, input_config in additional_inputs.items():

                    # Get table type options for this input port
                    if table_type_options and input_port in table_type_options:
                        table_columns = table_type_options[input_port]
                    else:
                        # Default options
                        table_columns = ["entity", "chebi_id"]

                    # Create appropriate column names based on table type
                    if len(table_columns) == 1:
                        # Only one option, it's medium table
                        table_columns = ["entity", "chebi_id"]
                        step_df = pd.DataFrame(columns=table_columns)

                    else:
                        # Multiple options, let user choose
                        choice_table_type = st.selectbox(
                            label=translate_service.translate("please_select_option"),
                            options=[col.replace('_', ' ').title() + " Table" for col in table_columns],
                            key=f"table_type_{input_port}"
                        )

                        # Map back to column name
                        if "ec" in choice_table_type.lower():
                            step_df = pd.DataFrame(columns=["ec_number"])
                        elif "entity" in choice_table_type.lower():
                            step_df = pd.DataFrame(columns=["id"])
                        else:
                            step_df = pd.DataFrame(columns=[table_columns[0]])

                    edited_step_df = st.data_editor(
                        step_df,
                        width="stretch",
                        hide_index=True,
                        num_rows="dynamic",
                        key=f"editor_{input_port}"
                    )

                    created_tables[input_port] = edited_step_df

    # Check if all required resources are selected or created
    all_resources_ready = True
    if additional_inputs:
        if type_resource_selection == translate_service.translate("select_resource"):
            for input_port in additional_inputs.keys():
                if input_port not in selected_resources:
                    all_resources_ready = False
                    break
        # For created tables, they're always ready (even if empty)

    form_config = StreamlitTaskRunner(task_class)
    form_config.generate_config_form_without_run(
        session_state_key=config_session_key,
        default_config_values=task_class.config_specs.get_default_values(),
        is_default_config_valid=task_class.config_specs.mandatory_values_are_set(
            task_class.config_specs.get_default_values()))

    if st.button(f"{task_name}", width="stretch", icon=":material/play_arrow:", key=f"button_{task_name.lower().replace(' ', '_')}"):
        # Get config using the provided getter method
        config_data = getattr(gena_state, config_getter_method)()

        if not config_data["is_valid"]:
            st.warning(translate_service.translate("fill_mandatory_fields"))
            return

        if additional_inputs and not all_resources_ready:
            st.warning(translate_service.translate("select_resource_warning"))
            return

        with st.spinner(f"Running {task_name}..."):
            with StreamlitAuthenticateUser():
                # Add the task to the scenario "Network"
                scenario = ScenarioProxy.from_existing_scenario(gena_state.get_scenario_step_network()[0].id)
                protocol = scenario.get_protocol()
                number_processes = len(protocol.get_model().processes)
                instance_name = f"{task_name.lower().replace(' ', '_')}_process_{number_processes}"

                process = protocol.add_process(task_class, instance_name, config_params=config_data["config"])

                # Retrieve the last output network and connect
                network_inport = protocol.get_process('network_process_output').get_first_inport()
                process_instance_name = network_inport.process_instance_name

                # Find the connector to the output
                protocol_model = protocol.get_model()
                connector = None
                for cnt in protocol_model.connectors:
                    if cnt.right_process.instance_name == process_instance_name:
                        connector = cnt
                        break

                # Delete the output process
                protocol.delete_process(process_instance_name)

                # Connect the previous process to the new task (network input)
                protocol.add_connector(
                    out_port=protocol.get_process(connector.left_process.instance_name) >> connector.left_port_name,
                    in_port=process << task_input_name_for_network
                )

                # Add additional resource inputs if any
                if additional_inputs:
                    for input_port, input_config in additional_inputs.items():
                        if type_resource_selection == translate_service.translate("create_new_resource"):
                            # Create new table resource
                            table_data = created_tables[input_port]
                            path_temp = os.path.join(os.path.abspath(os.path.dirname(__file__)), Settings.make_temp_dir())
                            full_path = os.path.join(path_temp, f"Table_{input_port}_{task_name}.csv")
                            table_file: File = File(full_path)
                            table_file.write(table_data.to_csv(index=False))
                            table_resource = TableImporter.call(File(full_path))
                            saved_table = ResourceModel.save_from_resource(
                                table_resource, ResourceOrigin.UPLOADED, flagged=True)
                            selected_table_id = saved_table.id
                        else:
                            selected_table_id = selected_resources[input_port]

                        # Add input task for the table
                        resource_input_name = f"{input_port}_input_{number_processes}"
                        resource_process = protocol.add_process(
                            InputTask, resource_input_name,
                            {InputTask.config_name: selected_table_id}
                        )
                        protocol.add_connector(
                            out_port=resource_process >> 'resource',
                            in_port=process << input_port
                        )

                # Add new output
                protocol.add_output('network_process_output', process >> 'network', flag_resource=False)
                scenario.add_to_queue()

                # Wait for the task to be completed
                ScenarioWaiterBasic(scenario.get_model_id()).wait_until_finished(refresh_interval=10, refresh_interval_max_count=100)
                protocol.refresh()
                scenario.refresh()

                # Get the updated network and save it
                if scenario.is_success():
                    new_network = protocol.get_process('network_process_output').get_input('resource')
                    gena_state.set_edited_network(new_network)
                    add_tags_on_network(gena_state.get_edited_network(), gena_state)
                else:
                    st.error(f"{task_name} {translate_service.translate('task_failed')} ")

        st.rerun()

@st.dialog("Run Reaction Adder")
def run_reaction_adder(gena_state: State):
    """Dialog for running Reaction Adder task."""
    translate_service = gena_state.get_translate_service()
    _run_network_editing_task(
        task_class=ReactionAdder,
        task_name=translate_service.translate("run_reaction_adder"),
        gena_state=gena_state,
        config_session_key=gena_state.REACTION_ADDER_CONFIG_KEY,
        config_getter_method="get_reaction_adder_config",
        additional_inputs={
            'reaction_table': {
                'session_key': gena_state.REACTION_ADDER_TABLE_SELECTOR_KEY,
                'placeholder': translate_service.translate('search_reaction_table')
            }
        },
        table_type_options={
            'reaction_table': ['ec_number', 'entity_id']
        }
    )

@st.dialog("Run Transporter Adder")
def run_transporter_adder(gena_state: State):
    """Dialog for running Transporter Adder task."""
    translate_service = gena_state.get_translate_service()
    _run_network_editing_task(
        task_class=TransporterAdder,
        task_name=translate_service.translate("run_transporter_adder"),
        gena_state=gena_state,
        config_session_key=gena_state.TRANSPORTER_ADDER_CONFIG_KEY,
        config_getter_method="get_transporter_adder_config",
        additional_inputs={
            'medium_table': {
                'session_key': gena_state.TRANSPORTER_TABLE_SELECTOR_KEY,
                'placeholder': translate_service.translate('search_medium_table')
            }
        },
        table_type_options={
            'medium_table': ['Medium table']
        }
    )

@st.dialog("Run Reaction Remover")
def run_reaction_remover(gena_state: State):
    """Dialog for running Reaction Remover task."""
    translate_service = gena_state.get_translate_service()
    _run_network_editing_task(
        task_class=ReactionRemover,
        task_name=translate_service.translate("run_reaction_remover"),
        gena_state=gena_state,
        config_session_key=gena_state.REACTION_REMOVER_CONFIG_KEY,
        config_getter_method="get_reaction_remover_config",
        additional_inputs={
            'reaction_table': {
                'session_key': gena_state.REACTION_REMOVER_TABLE_SELECTOR_KEY,
                'placeholder': translate_service.translate('search_medium_table')
            }
        },
        table_type_options={
            'reaction_table': ['ec_number', 'entity_id']
        }
    )

@st.dialog("Run Orphan Remover")
def run_orphan_remover(gena_state: State):
    """Dialog for running Orphan Remover task."""
    translate_service = gena_state.get_translate_service()
    _run_network_editing_task(
        task_class=OrphanRemover,
        task_name=translate_service.translate("run_orphan_remover"),
        gena_state=gena_state,
        config_session_key=gena_state.ORPHAN_REMOVER_CONFIG_KEY,
        config_getter_method="get_orphan_remover_config"
    )

@st.dialog("Run Network Mergem")
def run_network_mergem(gena_state: State):
    """Dialog for running Network Mergem task."""
    translate_service = gena_state.get_translate_service()
    _run_network_editing_task(
        task_class=NetworkMergem,
        task_name=translate_service.translate("run_network_mergem"),
        gena_state=gena_state,
        config_session_key=gena_state.NETWORK_MERGEM_CONFIG_KEY,
        config_getter_method="get_network_mergem_config",
        task_input_name_for_network = "network_1",
        additional_inputs={
            'network_2': {
                'session_key': gena_state.NETWORK_MERGEM_SELECTOR_KEY,
                'placeholder': translate_service.translate('search_network_merge')
            }
        }
    )

@st.dialog("Run Network Merger")
def run_network_merger(gena_state: State):
    """Dialog for running Network Merger task."""
    translate_service = gena_state.get_translate_service()
    _run_network_editing_task(
        task_class=NetworkMerger,
        task_name=translate_service.translate("run_network_merger"),
        gena_state=gena_state,
        config_session_key=gena_state.NETWORK_MERGER_CONFIG_KEY,
        config_getter_method="get_network_merger_config",
        task_input_name_for_network = "network_1",
        additional_inputs={
            'network_2': {
                'session_key': gena_state.NETWORK_MERGER_SELECTOR_KEY,
                'placeholder': translate_service.translate('search_network_merge')
            }
        }
    )

@st.dialog("Run Gap Filler")
def run_gap_filler(gena_state: State):
    """Dialog for running Gap Filler task."""
    translate_service = gena_state.get_translate_service()
    _run_network_editing_task(
        task_class=GapFiller,
        task_name=translate_service.translate("run_gap_filler"),
        gena_state=gena_state,
        config_session_key=gena_state.GAP_FILLER_CONFIG_KEY,
        config_getter_method="get_gap_filler_config"
    )


def render_network_step(selected_scenario: Scenario, gena_state: State) -> None:
    translate_service = gena_state.get_translate_service()
    if selected_scenario.status == ScenarioStatus.ERROR:
        st.warning(f"⚠️ {translate_service.translate('scenario_not_successful')}")
        return
    file_network_id = gena_state.get_resource_id_network()

    # Create 2 tabs : one to display the network, the other to have the history of the network
    tab_network, tab_history = st.tabs([translate_service.translate("network"), translate_service.translate("history")])

    if not gena_state.get_scenario_step_context():
        if not gena_state.get_is_standalone():
            with tab_network:
                title_col, button_col = StreamlitContainers.columns_with_fit_content('container-column', cols=[1, 'fit-content'],
                    vertical_align_items='center')
                with title_col:
                    st.markdown(f"### {translate_service.translate('edit_network')}")
                with button_col:

                    # Add a button menu to edit the network
                    button_menu = StreamlitMenuButton()

                    # Adder
                    buttons_adder = StreamlitMenuButtonItem(label=translate_service.translate('adder'), material_icon='add')
                    add_reaction_button = StreamlitMenuButtonItem(label=translate_service.translate('add_reaction'), material_icon='add',
                                                        on_click=lambda state=gena_state: run_reaction_adder(state))
                    add_transporter_button = StreamlitMenuButtonItem(label=translate_service.translate('add_transporter'), material_icon='add',
                                                        on_click=lambda state=gena_state: run_transporter_adder(state))
                    buttons_adder.add_children([add_reaction_button, add_transporter_button])
                    button_menu.add_button_item(buttons_adder)

                    # Remover
                    buttons_remover = StreamlitMenuButtonItem(label=translate_service.translate('remover'), material_icon='remove')
                    remove_reaction_button = StreamlitMenuButtonItem(label=translate_service.translate('remove_reaction'), material_icon='remove',
                                                                    on_click=lambda state=gena_state: run_reaction_remover(state))
                    remove_orphan_button = StreamlitMenuButtonItem(label=translate_service.translate('remove_orphan'), material_icon='remove',
                                                                    on_click=lambda state=gena_state: run_orphan_remover(state))
                    buttons_remover.add_children([remove_reaction_button, remove_orphan_button])
                    button_menu.add_button_item(buttons_remover)

                    # Merge
                    buttons_merge = StreamlitMenuButtonItem(label=translate_service.translate('merge'), material_icon='merge')
                    child_merge_merger= StreamlitMenuButtonItem(
                        label=translate_service.translate('network_merger'), material_icon='merge', on_click=lambda state=gena_state: run_network_merger(state))
                    child_merge_mergem = StreamlitMenuButtonItem(
                        label=translate_service.translate('network_mergem'), material_icon='merge', on_click=lambda state=gena_state: run_network_mergem(state))
                    buttons_merge.add_children([child_merge_merger, child_merge_mergem])
                    button_menu.add_button_item(buttons_merge)

                    # Gap filler
                    buttons_gap_filler = StreamlitMenuButtonItem(label=translate_service.translate('gap_filler'), material_icon='auto_fix_high', on_click=lambda state=gena_state: run_gap_filler(state))
                    button_menu.add_button_item(buttons_gap_filler)

                    button_menu.render()

                st.info(f"ℹ️ {translate_service.translate('network_edit_info')}")

                gena_state.set_edited_network(ResourceModel.get_by_id(file_network_id).get_resource())

    with tab_history:
        # Display the history of all processes in the protocol
        # Thus the user can see what has been done to the network
        scenario = ScenarioProxy.from_existing_scenario(gena_state.get_scenario_step_network()[0].id)
        protocol = scenario.get_protocol()
        all_processes = protocol.get_model().get_all_processes_flatten_sort_by_start_date()
        display_process_history(all_processes, gena_state)

    with tab_network:
        display_network(file_network_id)

    # Save button only appear if Context task have not been created
    if not gena_state.get_scenario_step_context():
        if not gena_state.get_is_standalone():

            if st.button(translate_service.translate("save"), width="stretch"):
                with StreamlitAuthenticateUser():
                    # Use the helper function to save
                    add_tags_on_network(gena_state.get_edited_network(), gena_state)
                    st.rerun()
        else:
            st.info(f"ℹ️ {translate_service.translate('standalone_network_info')}")
    else:
        st.info(f"ℹ️ {translate_service.translate('network_locked_info')}")