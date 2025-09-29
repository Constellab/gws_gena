from typing import List, Dict
import streamlit as st
import pandas as pd

from gws_core import Scenario, ResourceModel
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.streamlit import StreamlitTranslateLang, StreamlitTranslateService

class State:
    """Class to manage the state of the app.
    """

    TAG_BRICK = "brick"
    TAG_GENA = "gena"
    TAG_SEQUENCING_TYPE = "sequencing_type"
    TAG_ANALYSIS_NAME = "analysis_name"

    # step tags
    TAG_NETWORK = "network"
    TAG_CONTEXT = "context"
    TAG_TWIN_BUILDER = "twin_builder"
    TAG_FBA = "fba"
    TAG_FVA = "fva"
    TAG_KOA = "koa"

    # Tags unique ids
    TAG_GENA_PIPELINE_ID = "gena_pipeline_id"
    TAG_TWIN_BUILDER_ID = "twin_builder_id"

    # Scenario names
    TWIN_SCENARIO_NAME_INPUT_KEY = "twin_scenario_name_input"
    FBA_SCENARIO_NAME_INPUT_KEY = "fba_scenario_name_input"
    FVA_SCENARIO_NAME_INPUT_KEY = "fva_scenario_name_input"
    KOA_SCENARIO_NAME_INPUT_KEY = "koa_scenario_name_input"


    SELECTED_SCENARIO_KEY = "selected_scenario"
    SELECTED_ANALYSIS_KEY = "selected_analysis"
    STEP_PIPELINE_KEY = "step_pipeline"
    SELECTED_FOLDER_ID_KEY = "selected_folder_id"
    RESOURCE_ID_NETWORK_KEY = "resource_id_network"
    RESOURCE_ID_CONTEXT_KEY = "resource_id_context"
    TAG_NETWORK_UPDATED = "network_updated"
    SCENARIOS_BY_STEP_KEY = "scenarios_by_step"
    CONTEXT_BOOL_KEY = "context_bool"
    CONTEXT_OPTION_KEY = "context_option"
    NETWORK_OPTION_KEY = "network_option"

    TREE_DEFAULT_ITEM_KEY = "tree_default_item"

    EDITED_NETWORK = "edited_network"
    STANDALONE_KEY = "standalone"

    ASSOCIATE_FOLDER_KEY = "associate_folder"

    RESOURCE_SELECTOR_NETWORK_KEY = "resource_selector_network"
    RESOURCE_SELECTOR_CONTEXT_KEY = "resource_selector_context"
    RESOURCE_SELECTOR_KO_TABLE_KEY = "resource_selector_ko_table"
    RESOURCE_SELECTOR_PHENOTYPE_KEY = "resource_selector_phenotype"
    RESOURCE_SELECTOR_FLUX_KEY = "resource_selector_flux"
    REACTION_ADDER_TABLE_SELECTOR_KEY = "reaction_adder_table_selector"
    REACTION_REMOVER_TABLE_SELECTOR_KEY = "reaction_remover_table_selector"
    TRANSPORTER_TABLE_SELECTOR_KEY = "transporter_table_selector"
    NETWORK_MERGEM_SELECTOR_KEY = "network_mergem_selector"
    NETWORK_MERGER_SELECTOR_KEY = "network_merger_selector"
    ANALYSIS_NAME_USER = "analysis_name_user"

    # Tree
    TREE_ANALYSIS_OBJECT = "analysis_tree_menu_object"
    TREE_ANALYSIS_KEY = "analysis_tree_menu"

    # Config keys
    NETWORK_IMPORTER_CONFIG_KEY = "network_importer_config"
    LOAD_BIGG_MODEL_CONFIG_KEY = "load_bigg_model_config"
    GAP_FILLER_CONFIG_KEY = "gap_filler_config"
    NETWORK_MERGER_CONFIG_KEY = "network_merger_config"
    REACTION_ADDER_CONFIG_KEY = "reaction_adder_config"
    TRANSPORTER_ADDER_CONFIG_KEY = "transporter_adder_config"
    REACTION_REMOVER_CONFIG_KEY = "reaction_remover_config"
    ORPHAN_REMOVER_CONFIG_KEY = "orphan_remover_config"
    NETWORK_MERGEM_CONFIG_KEY = "network_mergem_config"
    TWIN_BUILDER_CONFIG_KEY = "twin_builder_config"
    FBA_CONFIG_KEY = "fba_config"
    FVA_CONFIG_KEY = "fva_config"
    KOA_CONFIG_KEY = "koa_config"

    LANG_KEY = "lang_select"
    TRANSLATE_SERVICE = "translate_service"

    def __init__(cls, file_lang: str):
        translate_service = StreamlitTranslateService(file_lang)
        st.session_state[cls.TRANSLATE_SERVICE] = translate_service

    @classmethod
    def get_is_standalone(cls) -> bool:
        return st.session_state.get(cls.STANDALONE_KEY, False)

    @classmethod
    def set_is_standalone(cls, value: bool) -> None:
        st.session_state[cls.STANDALONE_KEY] = value

    @classmethod
    def get_lang(cls) -> StreamlitTranslateLang:
        # Get language from translate service instead of session state
        translate_service = cls.get_translate_service()
        if translate_service:
            return translate_service.get_lang()
        return StreamlitTranslateLang.EN  # Default to English

    @classmethod
    def set_lang(cls, value: StreamlitTranslateLang) -> None:
        # Update the translate service language instead of storing separately
        translate_service = cls.get_translate_service()
        if translate_service:
            translate_service.change_lang(value)
            cls.set_translate_service(translate_service)

    @classmethod
    def get_translate_service(cls):
        return st.session_state.get(cls.TRANSLATE_SERVICE, None)

    @classmethod
    def set_translate_service(cls, value : StreamlitTranslateService) -> None:
        st.session_state[cls.TRANSLATE_SERVICE] = value

    @classmethod
    def get_tree_default_item(cls) -> str:
        return st.session_state.get(cls.TREE_DEFAULT_ITEM_KEY, None)

    @classmethod
    def set_tree_default_item(cls, value: str) -> None:
        st.session_state[cls.TREE_DEFAULT_ITEM_KEY] = value

    @classmethod
    def set_associate_scenario_with_folder(cls, value: bool) -> None:
        st.session_state[cls.ASSOCIATE_FOLDER_KEY] = value

    @classmethod
    def get_associate_scenario_with_folder(cls) -> bool:
        return st.session_state.get(cls.ASSOCIATE_FOLDER_KEY, False)

    @classmethod
    def reset_tree_analysis(cls) -> None:
        """Reset the analysis tree state in session."""
        if cls.TREE_ANALYSIS_KEY in st.session_state:
            del st.session_state[cls.TREE_ANALYSIS_KEY]

    @classmethod
    def check_if_required_is_filled(cls, valeur: str) -> bool:
        if not valeur:
            return False
        return True

    @classmethod
    def get_edited_network(cls)-> str:
        return st.session_state.get(cls.EDITED_NETWORK, None)

    @classmethod
    def set_edited_network(cls, df_network : pd.DataFrame) -> None:
        st.session_state[cls.EDITED_NETWORK] = df_network

    @classmethod
    def get_context_bool(cls) -> str:
        return st.session_state.get(cls.CONTEXT_BOOL_KEY, None)

    @classmethod
    def get_context_option(cls) -> str:
        return st.session_state.get(cls.CONTEXT_OPTION_KEY, None)

    @classmethod
    def get_network_option(cls) -> str:
        return st.session_state.get(cls.NETWORK_OPTION_KEY, None)

    @classmethod
    def get_resource_selector_network(cls) -> ResourceModel:
        return st.session_state.get(cls.RESOURCE_SELECTOR_NETWORK_KEY, None)

    @classmethod
    def get_resource_selector_context(cls) -> ResourceModel:
        return st.session_state.get(cls.RESOURCE_SELECTOR_CONTEXT_KEY, None)

    @classmethod
    def get_resource_selector_ko_table(cls) -> ResourceModel:
        return st.session_state.get(cls.RESOURCE_SELECTOR_KO_TABLE_KEY, None)

    @classmethod
    def get_resource_selector_phenotype(cls) -> ResourceModel:
        return st.session_state.get(cls.RESOURCE_SELECTOR_PHENOTYPE_KEY, None)

    @classmethod
    def get_resource_selector_flux(cls) -> ResourceModel:
        return st.session_state.get(cls.RESOURCE_SELECTOR_FLUX_KEY, None)

    @classmethod
    def get_reaction_adder_table_selector(cls) -> ResourceModel:
        return st.session_state.get(cls.REACTION_ADDER_TABLE_SELECTOR_KEY, None)

    @classmethod
    def get_reaction_remover_table_selector(cls) -> ResourceModel:
        return st.session_state.get(cls.REACTION_REMOVER_TABLE_SELECTOR_KEY, None)

    @classmethod
    def get_transporter_table_selector(cls) -> ResourceModel:
        return st.session_state.get(cls.TRANSPORTER_TABLE_SELECTOR_KEY, None)

    @classmethod
    def get_network_mergem_selector(cls) -> ResourceModel:
        return st.session_state.get(cls.NETWORK_MERGEM_SELECTOR_KEY, None)

    @classmethod
    def get_network_merger_selector(cls) -> ResourceModel:
        return st.session_state.get(cls.NETWORK_MERGER_SELECTOR_KEY, None)

    @classmethod
    def get_analysis_name_user(cls) -> str:
        return st.session_state.get(cls.ANALYSIS_NAME_USER, None)

    @classmethod
    def set_selected_scenario(cls, scenario: Scenario):
        st.session_state[cls.SELECTED_SCENARIO_KEY] = scenario

    @classmethod
    def get_selected_scenario(cls) -> Scenario:
        return st.session_state.get(cls.SELECTED_SCENARIO_KEY)

    @classmethod
    # It's the network scenario
    def set_selected_analysis(cls, scenario: Scenario):
        st.session_state[cls.SELECTED_ANALYSIS_KEY] = scenario

    @classmethod
    def get_selected_analysis(cls) -> Scenario:
        return st.session_state.get(cls.SELECTED_ANALYSIS_KEY)

    # Infos of the network scenario
    @classmethod
    def get_current_tag_value_by_key(cls, key: str) -> str:
        network_scenario : Scenario = cls.get_selected_analysis()
        entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, network_scenario.id)
        tag = entity_tag_list.get_tags_by_key(key)[0].to_simple_tag()
        return tag.value

    @classmethod
    def get_current_gena_pipeline_id(cls) -> str:
        return cls.get_current_tag_value_by_key(cls.TAG_GENA_PIPELINE_ID)

    @classmethod
    def get_current_analysis_name(cls) -> str:
        return cls.get_current_tag_value_by_key(cls.TAG_ANALYSIS_NAME)

    @classmethod
    def get_resource_id_network(cls) -> str:
        return st.session_state.get(cls.RESOURCE_ID_NETWORK_KEY)

    @classmethod
    def set_resource_id_network(cls, resource_id: str):
        st.session_state[cls.RESOURCE_ID_NETWORK_KEY] = resource_id

    @classmethod
    def get_resource_id_context(cls) -> str:
        return st.session_state.get(cls.RESOURCE_ID_CONTEXT_KEY)

    @classmethod
    def set_resource_id_context(cls, resource_id: str):
        st.session_state[cls.RESOURCE_ID_CONTEXT_KEY] = resource_id

    @classmethod
    def set_step_pipeline(cls, step_name: str):
        st.session_state[cls.STEP_PIPELINE_KEY] = step_name

    @classmethod
    def get_step_pipeline(cls) -> str:
        return st.session_state.get(cls.STEP_PIPELINE_KEY)

    @classmethod
    def set_selected_folder_id(cls, folder_id: str):
        st.session_state[cls.SELECTED_FOLDER_ID_KEY] = folder_id

    @classmethod
    def get_selected_folder_id(cls) -> str:
        return st.session_state.get(cls.SELECTED_FOLDER_ID_KEY)

    @classmethod
    def get_scenario_user_name(cls, key: str) -> str:
        return st.session_state.get(key, "")

    # Functions get config

    @classmethod
    def get_network_importer_config(cls) -> Dict:
        return st.session_state.get(cls.NETWORK_IMPORTER_CONFIG_KEY, {})

    @classmethod
    def get_load_bigg_model_config(cls) -> Dict:
        return st.session_state.get(cls.LOAD_BIGG_MODEL_CONFIG_KEY, {})

    @classmethod
    def get_gap_filler_config(cls) -> Dict:
        return st.session_state.get(cls.GAP_FILLER_CONFIG_KEY, {})

    @classmethod
    def get_network_merger_config(cls) -> Dict:
        return st.session_state.get(cls.NETWORK_MERGER_CONFIG_KEY, {})

    @classmethod
    def get_network_mergem_config(cls) -> Dict:
        return st.session_state.get(cls.NETWORK_MERGEM_CONFIG_KEY, {})

    @classmethod
    def get_reaction_adder_config(cls) -> Dict:
        return st.session_state.get(cls.REACTION_ADDER_CONFIG_KEY, {})

    @classmethod
    def get_transporter_adder_config(cls) -> Dict:
        return st.session_state.get(cls.TRANSPORTER_ADDER_CONFIG_KEY, {})

    @classmethod
    def get_reaction_remover_config(cls) -> Dict:
        return st.session_state.get(cls.REACTION_REMOVER_CONFIG_KEY, {})

    @classmethod
    def get_orphan_remover_config(cls) -> Dict:
        return st.session_state.get(cls.ORPHAN_REMOVER_CONFIG_KEY, {})

    @classmethod
    def get_twin_builder_config(cls) -> Dict:
        return st.session_state.get(cls.TWIN_BUILDER_CONFIG_KEY, {})

    @classmethod
    def get_fba_config(cls) -> Dict:
        return st.session_state.get(cls.FBA_CONFIG_KEY, {})

    @classmethod
    def get_fva_config(cls) -> Dict:
        return st.session_state.get(cls.FVA_CONFIG_KEY, {})

    @classmethod
    def get_koa_config(cls) -> Dict:
        return st.session_state.get(cls.KOA_CONFIG_KEY, {})

    # Get scenarios ids of each step
    @classmethod
    def get_scenarios_by_step_dict(cls) -> Dict:
        return st.session_state.get(cls.SCENARIOS_BY_STEP_KEY, {})

    @classmethod
    def set_scenarios_by_step_dict(cls, scenarios_by_step: Dict) -> None:
        st.session_state[cls.SCENARIOS_BY_STEP_KEY] = scenarios_by_step

    @classmethod
    def get_scenario_step_network(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_NETWORK)

    @classmethod
    def get_scenario_step_context(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_CONTEXT)

    @classmethod
    def get_scenario_step_twin_builder(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_TWIN_BUILDER)

    @classmethod
    def get_scenario_step_fba(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_FBA, [])

    @classmethod
    def get_scenario_step_fva(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_FVA, [])

    @classmethod
    def get_scenario_step_koa(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_KOA, [])

    @classmethod
    def get_tree_menu_object(cls):
        """Get the tree menu instance from session state."""
        return st.session_state.get(cls.TREE_ANALYSIS_OBJECT)

    @classmethod
    def set_tree_menu_object(cls, tree_menu_object) -> None:
        st.session_state[cls.TREE_ANALYSIS_OBJECT] = tree_menu_object

    @classmethod
    def update_tree_menu_selection(cls, item_key: str):
        """Update the tree menu selection if tree menu instance exists."""
        tree_menu = cls.get_tree_menu_object()
        if tree_menu:
            tree_menu.set_selected_item(item_key)