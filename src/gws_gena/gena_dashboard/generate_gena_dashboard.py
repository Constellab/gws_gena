from gws_core import (ConfigParams, AppConfig, AppType, OutputSpec,
                      OutputSpecs, StreamlitResource, Task, TaskInputs,
                      CredentialsDataLab, CredentialsParam, CredentialsType,
                      TaskOutputs, app_decorator, task_decorator,
                      InputSpecs, ConfigSpecs, BoolParam)


@app_decorator("GenaDashboardAppConfig", app_type=AppType.STREAMLIT,
               human_name="Generate Gena Dashboard app")
class GenaDashboardAppConfig(AppConfig):
    """
    Configuration class for the Gena Dashboard Streamlit application.

    This class defines the configuration and setup for a Streamlit-based dashboard
    that provides visualization and analysis capabilities for digital twin.
    """

    # retrieve the path of the app folder, relative to this file
    # the app code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(__file__, "_gena_dashboard")


@task_decorator("GenerateGenaDashboard", human_name="Generate Gena Dashboard app",
                style=StreamlitResource.copy_style())
class GenerateGenaDashboard(Task):
    """
    Task that generates the Gena Dashboard app.
    This dashboard provides visualization and analysis capabilities for digital twin.
    The Gena Dashboard is a Streamlit application designed for digital twin analysis and visualization. It provides an interactive interface for processing, analyzing, and interpreting digital twin data through various bioinformatics workflows.

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
    ),
    'credentials_lab_large' : CredentialsParam(
        credentials_type=CredentialsType.LAB, human_name="Credentials lab large to run 16s step", short_description="Credentials to request lab large's API", optional = True)})


    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        credentials_data: CredentialsDataLab = params.get_value(
            'credentials_lab_large')

        """ Run the task """

        streamlit_app = StreamlitResource()

        streamlit_app.set_app_config(GenaDashboardAppConfig())
        streamlit_app.name = "Gena Dashboard"

        # Add param
        associate_scenario_with_folder: bool = params.get_value(
            'associate_scenario_with_folder')
        streamlit_app.set_param(
            'associate_scenario_with_folder', associate_scenario_with_folder)
        if credentials_data:
            streamlit_app.set_param(
                "credentials_name", credentials_data.meta.name)

        return {"streamlit_app": streamlit_app}
