import os

from gws_core import (
    AppConfig,
    AppType,
    ConfigParams,
    OutputSpec,
    OutputSpecs,
    StreamlitResource,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingStyle,
    app_decorator,
    task_decorator,
)


@app_decorator("GenaStandaloneDashboard", app_type=AppType.STREAMLIT)
class GenaStandaloneDashboardClass(AppConfig):
    def get_app_folder_path(self):
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), "_gena_standalone")


@task_decorator(
    "GenaStandaloneDashboard",
    human_name="Standalone Constellab Digital Twin",
    short_description="Standalone Streamlit dashboard for Constellab Digital Twin",
    style=TypingStyle.community_icon(icon_technical_name="dashboard", background_color="#178394"),
)
class GenaStandaloneDashboard(Task):
    """
    Standalone Constellab Digital Twin. No data is stored.

    This dashboard provides visualization for digital twins.

    The Constellab Digital Twin app is a Streamlit application designed for digital twins visualization.

    The aim is to simplify the use of the Gena Brick by providing an application that makes retrieving results easier. Dependencies between scenarios are also maintained, allowing you to navigate more easily.

    Multi-Step Analysis Pipeline

    The dashboard implements a structured analysis workflow with the following steps:

    """

    output_specs: OutputSpecs = OutputSpecs(
        {
            "streamlit_app": OutputSpec(
                StreamlitResource, human_name="Standalone Variant Detection dashboard"
            )
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        streamlit_app = StreamlitResource()
        streamlit_app.set_app_config(GenaStandaloneDashboardClass())
        streamlit_app.name = "Constellab Digital Twin Standalone"

        streamlit_app.set_requires_authentication(False)
        return {"streamlit_app": streamlit_app}
