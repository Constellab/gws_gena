from gws_core import (ConfigParams, AppConfig, AppType, OutputSpec,
                      OutputSpecs, StreamlitResource, Task, TaskInputs,
                      TaskOutputs, app_decorator, task_decorator,
                      InputSpecs, ConfigSpecs, BoolParam)


@app_decorator("GenaDashboardAppConfig", app_type=AppType.STREAMLIT,
               human_name="Generate Constellab Digital Twin app")
class GenaDashboardAppConfig(AppConfig):
    """
    Configuration class for the Constellab Digital Twin app Streamlit application.

    This class defines the configuration and setup for a Streamlit-based dashboard
    that provides visualization and analysis capabilities for digital twin.
    """

    # retrieve the path of the app folder, relative to this file
    # the app code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(__file__, "_gena_dashboard")


@task_decorator("GenerateGenaDashboard", human_name="Generate Constellab Digital Twin app",
                style=StreamlitResource.copy_style())
class GenerateGenaDashboard(Task):
    """
    Task that generates the Constellab Digital Twin app.
    This dashboard provides visualization and analysis capabilities for digital twin.
    The Constellab Digital Twin app is a Streamlit application designed for digital twin analysis and visualization. It provides an interactive interface for processing, analyzing, and interpreting digital twin data through various bioinformatics workflows.

    The aim is to simplify the use of the Gena Brick by providing an application that makes running the pipeline and retrieving results easier. Dependencies between scenarios are also maintained, allowing you to navigate more easily.

    Multi-Step Analysis Pipeline

    The dashboard implements a structured analysis workflow with the following steps:


    """

    input_specs = InputSpecs()
    output_specs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource)
    })

    config_specs : ConfigSpecs = ConfigSpecs({'associate_scenario_with_folder': BoolParam(
        default_value=False, human_name="Associate Scenario with Folder", short_description="Set to True if it is mandatory to associate scenarios with a folder."
    )})


    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        """ Run the task """

        streamlit_app = StreamlitResource()

        streamlit_app.set_app_config(GenaDashboardAppConfig())
        streamlit_app.name = "Constellab Digital Twin"

        # Add param
        associate_scenario_with_folder: bool = params.get_value(
            'associate_scenario_with_folder')
        streamlit_app.set_param(
            'associate_scenario_with_folder', associate_scenario_with_folder)

        return {"streamlit_app": streamlit_app}
