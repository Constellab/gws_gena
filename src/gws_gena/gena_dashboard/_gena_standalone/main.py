import streamlit as st
from gws_gena.gena_dashboard._gena_dashboard_core.pages import first_page, new_analysis_page, analysis_page
from gws_gena.gena_dashboard._gena_dashboard_core.state import State
from gws_core.streamlit import StreamlitRouter

if 'standalone' not in st.session_state:
    st.subheader("Welcome to the Gena Standalone Dashboard!")
    st.write("This application is intended exclusively for **visualization**.")
    st.write("The Gena Dashboard is a Streamlit application designed for digital twin analysis and visualization. It provides an interactive interface for processing, analyzing, and interpreting digital twins through various bioinformatics workflows.")
    st.write("This standalone dashboard only allows users to visualise results that have already been run. However, don't hesitate to contact us to arrange a demo of the full app, in which we can also run analyses automatically!")
    st.write("Click on the button to launch the app: ")

    if st.button("Launch the app"):
        # Set the attribute to indicate that this is a standalone dashboard
        st.session_state['standalone'] = True
        st.rerun()

else:
    gena_state = State()
    gena_state.set_associate_scenario_with_folder(False)
    gena_state.set_is_standalone(True)

    # Hide sidebar completely
    st.markdown("""
    <style>
    .stSidebar, [data-testid="stSidebarCollapsedControl"]{
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

    def display_first_page(gena_state : State):
        first_page.render_first_page(gena_state)

    def add_first_page(router: StreamlitRouter, gena_state: State):
        router.add_page(
            lambda: display_first_page(gena_state),
            title='First page',
            url_path='first-page',
            icon='📦',
            hide_from_sidebar=True
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

    router = StreamlitRouter.load_from_session()
    # Add pages
    add_first_page(router, gena_state)
    add_new_analysis_page(router, gena_state)
    add_analysis_page(router, gena_state)


    router.run()

