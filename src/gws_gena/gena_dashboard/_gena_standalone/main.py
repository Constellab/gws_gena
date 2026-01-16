import os

from gws_core.streamlit import StreamlitRouter
from gws_gena.gena_dashboard._gena_dashboard_core.pages import (
    analysis_page,
    first_page,
    new_analysis_page,
    settings,
)
from gws_gena.gena_dashboard._gena_dashboard_core.state import State

# Path of the folder containing the translation files
lang_translation_folder_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../_gena_dashboard_core')
gena_state = State(lang_translation_folder_path)
gena_state.set_associate_scenario_with_folder(False)
gena_state.set_is_standalone(True)

def display_first_page(gena_state : State):
    first_page.render_first_page(gena_state)

def add_first_page(router: StreamlitRouter, gena_state: State):
    translate_service = gena_state.get_translate_service()
    router.add_page(
        lambda: display_first_page(gena_state),
        title=translate_service.translate('page_recipes'),
        url_path='first-page',
        icon='📦',
        hide_from_sidebar=False
    )

def display_new_analysis_page(gena_state : State):
    new_analysis_page.render_new_analysis_page(gena_state)

def add_new_analysis_page(router: StreamlitRouter, gena_state: State):
    router.add_page(
        lambda: display_new_analysis_page(gena_state),
        title='New Analysis',
        url_path='new-analysis',
        icon=":material/edit_note:",
        hide_from_sidebar=True
    )

def display_analysis_page(gena_state : State):
    analysis_page.render_analysis_page(gena_state)

def add_analysis_page(router: StreamlitRouter, gena_state: State):
    router.add_page(
        lambda: display_analysis_page(gena_state),
        title='Analysis',
        url_path='analysis',
        icon=":material/analytics:",
        hide_from_sidebar=True
    )

def display_settings_page(gena_state : State):
    settings.render_settings_page(gena_state)

def add_settings_page(router: StreamlitRouter, gena_state: State):
    translate_service = gena_state.get_translate_service()
    router.add_page(
        lambda: display_settings_page(gena_state),
        title=translate_service.translate('page_settings'),
        url_path='settings',
        icon=":material/settings:",
        hide_from_sidebar=False
    )

router = StreamlitRouter.load_from_session()
# Add pages
add_first_page(router, gena_state)
add_new_analysis_page(router, gena_state)
add_analysis_page(router, gena_state)
add_settings_page(router, gena_state)

router.run()

