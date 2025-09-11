import streamlit as st
from typing import Type, Dict, Optional, List
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner, StreamlitMenuButton, StreamlitMenuButtonItem, StreamlitContainers, StreamlitResourceSelect
from gws_core import ScenarioStatus, Scenario, ResourceModel, ScenarioProxy, Scenario, ScenarioWaiterBasic, InputTask
from gws_gena.gena_dashboard._gena_dashboard_core.functions_steps import display_network, search_updated_network, save_network
from gws_gena import Network, GapFiller, ReactionAdder, ReactionRemover, OrphanRemover, NetworkMerger, IsolateFinder, NetworkMergem, TransporterAdder
from gws_core.task.task import Task


def _run_network_editing_task(
    task_class: Type[Task],
    task_name: str,
    gena_state: State,
    config_session_key: str,
    config_getter_method: str,
    task_input_name_for_network: str = 'network',
    additional_inputs: Optional[Dict[str, Dict[str, str]]] = None
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
    """
    # Handle additional resource inputs
    selected_resources = {}
    if additional_inputs:
        st.markdown("#### Select Additional Resources")
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

    # Check if all required resources are selected
    all_resources_selected = True
    if additional_inputs:
        for input_port in additional_inputs.keys():
            if input_port not in selected_resources:
                all_resources_selected = False
                break

    form_config = StreamlitTaskRunner(task_class)
    form_config.generate_config_form_without_run(
        session_state_key=config_session_key,
        default_config_values=task_class.config_specs.get_default_values(),
        is_default_config_valid=task_class.config_specs.mandatory_values_are_set(
            task_class.config_specs.get_default_values()))

    if st.button(f"Run {task_name}", use_container_width=True, icon=":material/play_arrow:", key=f"button_{task_name.lower().replace(' ', '_')}"):
        # Get config using the provided getter method
        config_data = getattr(gena_state, config_getter_method)()

        if not config_data["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        if additional_inputs and not all_resources_selected:
            st.warning("Please select all required resources.")
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
                    for input_port, resource_id in selected_resources.items():
                        resource_input_name = f"{input_port}_input_{number_processes}"
                        resource_process = protocol.add_process(
                            InputTask, resource_input_name,
                            {InputTask.config_name: resource_id}
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
                    save_network(gena_state.get_edited_network(), gena_state)
                else:
                    st.error(f"{task_name} task failed. Please check the scenario details in your lab.")

        st.rerun()

@st.dialog("Run Reaction Adder")
def run_reaction_adder(gena_state: State):
    """Dialog for running Reaction Adder task."""
    _run_network_editing_task(
        task_class=ReactionAdder,
        task_name="Reaction Adder",
        gena_state=gena_state,
        config_session_key=gena_state.REACTION_ADDER_CONFIG_KEY,
        config_getter_method="get_reaction_adder_config",
        additional_inputs={
            'reaction_table': {
                'session_key': gena_state.REACTION_ADDER_TABLE_SELECTOR_KEY,
                'placeholder': 'Search for reaction table resource'
            }
        }
    )

@st.dialog("Run Transporter Adder")
def run_transporter_adder(gena_state: State):
    """Dialog for running Transporter Adder task."""
    _run_network_editing_task(
        task_class=TransporterAdder,
        task_name="Transporter Adder",
        gena_state=gena_state,
        config_session_key=gena_state.TRANSPORTER_ADDER_CONFIG_KEY,
        config_getter_method="get_transporter_adder_config",
        additional_inputs={
            'medium_table': {
                'session_key': gena_state.TRANSPORTER_TABLE_SELECTOR_KEY,
                'placeholder': 'Search for medium table resource'
            }
        }
    )

@st.dialog("Run Reaction Remover")
def run_reaction_remover(gena_state: State):
    """Dialog for running Reaction Remover task."""
    _run_network_editing_task(
        task_class=ReactionRemover,
        task_name="Reaction Remover",
        gena_state=gena_state,
        config_session_key=gena_state.REACTION_REMOVER_CONFIG_KEY,
        config_getter_method="get_reaction_remover_config",
        additional_inputs={
            'reaction_table': {
                'session_key': gena_state.REACTION_REMOVER_TABLE_SELECTOR_KEY,
                'placeholder': 'Search for medium table resource'
            }
        }
    )

@st.dialog("Run Orphan Remover")
def run_orphan_remover(gena_state: State):
    """Dialog for running Orphan Remover task."""
    _run_network_editing_task(
        task_class=OrphanRemover,
        task_name="Orphan Remover",
        gena_state=gena_state,
        config_session_key=gena_state.ORPHAN_REMOVER_CONFIG_KEY,
        config_getter_method="get_orphan_remover_config"
    )

@st.dialog("Run Network Mergem")
def run_network_mergem(gena_state: State):
    """Dialog for running Network Mergem task."""
    _run_network_editing_task(
        task_class=NetworkMergem,
        task_name="Network Mergem",
        gena_state=gena_state,
        config_session_key=gena_state.NETWORK_MERGEM_CONFIG_KEY,
        config_getter_method="get_network_mergem_config",
        task_input_name_for_network = "network_1",
        additional_inputs={
            'network_2': {
                'session_key': gena_state.NETWORK_MERGEM_SELECTOR_KEY,
                'placeholder': 'Search for network to merge resource'
            }
        }
    )

@st.dialog("Run Network Merger")
def run_network_merger(gena_state: State):
    """Dialog for running Network Merger task."""
    _run_network_editing_task(
        task_class=NetworkMerger,
        task_name="Network Merger",
        gena_state=gena_state,
        config_session_key=gena_state.NETWORK_MERGER_CONFIG_KEY,
        config_getter_method="get_network_merger_config",
        task_input_name_for_network = "network_1",
        additional_inputs={
            'network_2': {
                'session_key': gena_state.NETWORK_MERGER_SELECTOR_KEY,
                'placeholder': 'Search for network to merge resource'
            }
        }
    )

@st.dialog("Run Gap Filler")
def run_gap_filler(gena_state: State):
    """Dialog for running Gap Filler task."""
    _run_network_editing_task(
        task_class=GapFiller,
        task_name="Gap Filler",
        gena_state=gena_state,
        config_session_key=gena_state.GAP_FILLER_CONFIG_KEY,
        config_getter_method="get_gap_filler_config"
    )


def render_network_step(selected_scenario: Scenario, gena_state: State) -> None:
    if selected_scenario.status == ScenarioStatus.ERROR:
        st.warning("⚠️ Selected scenario is not successful. Check the scenario details in your lab.")
        return
    file_network_id = gena_state.get_resource_id_network()

    if not gena_state.get_scenario_step_context():
        if not gena_state.get_is_standalone():
            title_col, button_col = StreamlitContainers.columns_with_fit_content('container-column', cols=[1, 'fit-content'],
                vertical_align_items='center')
            with title_col:
                st.markdown("### Edit network")
            with button_col:

                # Add a button menu to edit the network
                button_menu = StreamlitMenuButton()

                # Adder
                buttons_adder = StreamlitMenuButtonItem(label='Adder', material_icon='add')
                add_reaction_button = StreamlitMenuButtonItem(label='Add reaction', material_icon='add',
                                                    on_click=lambda state=gena_state: run_reaction_adder(state))
                add_transporter_button = StreamlitMenuButtonItem(label='Add transporter', material_icon='add',
                                                    on_click=lambda state=gena_state: run_transporter_adder(state))
                buttons_adder.add_children([add_reaction_button, add_transporter_button])
                button_menu.add_button_item(buttons_adder)

                # Remover
                buttons_remover = StreamlitMenuButtonItem(label='Remover', material_icon='remove')
                remove_reaction_button = StreamlitMenuButtonItem(label='Remove reaction', material_icon='remove',
                                                                  on_click=lambda state=gena_state: run_reaction_remover(state))
                remove_orphan_button = StreamlitMenuButtonItem(label='Remove orphan', material_icon='remove',
                                                                  on_click=lambda state=gena_state: run_orphan_remover(state))
                buttons_remover.add_children([remove_reaction_button, remove_orphan_button])
                button_menu.add_button_item(buttons_remover)

                # Merge
                buttons_merge = StreamlitMenuButtonItem(label='Merge', material_icon='merge')
                child_merge_merger= StreamlitMenuButtonItem(
                    label='Network merger', material_icon='merge', on_click=lambda state=gena_state: run_network_merger(state))
                child_merge_mergem = StreamlitMenuButtonItem(
                    label='Network mergem', material_icon='merge', on_click=lambda state=gena_state: run_network_mergem(state))
                buttons_merge.add_children([child_merge_merger, child_merge_mergem])
                button_menu.add_button_item(buttons_merge)

                # Gap filler
                buttons_gap_filler = StreamlitMenuButtonItem(label='Gap filler', material_icon='auto_fix_high', on_click=lambda state=gena_state: run_gap_filler(state))
                button_menu.add_button_item(buttons_gap_filler)

                button_menu.render()

            st.info("ℹ️ You can edit the network before running Context. Once Context is run, the network will be locked.")

            gena_state.set_edited_network(ResourceModel.get_by_id(file_network_id).get_resource())
            display_network(file_network_id)


        else:
            st.markdown("### View network")
            display_network(file_network_id)
    else:
        st.markdown("### View network")
        display_network(file_network_id)

    # Save button only appear if Context task have not been created
    if not gena_state.get_scenario_step_context():
        if not gena_state.get_is_standalone():

            if st.button("Save", use_container_width=True):
                with StreamlitAuthenticateUser():
                    # Use the helper function to save
                    save_network(gena_state.get_edited_network(), gena_state)
                    st.rerun()
        else:
            st.info("ℹ️ You are in standalone mode. Network cannot be edited.")
    else:
        st.info("ℹ️ Network is locked because Context has already been run.")