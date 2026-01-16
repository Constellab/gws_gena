import os

from gws_core import (
    ConfigParams,
    ConfigSpecs,
    File,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingStyle,
    task_decorator,
)

from ..cobra_env import CobraEnvHelper


@task_decorator("ConvertXmlToJson", human_name="XML/Matlab to JSON",
                short_description="This task converts a xml file or a matlab file into a json file",
                style=TypingStyle.material_icon(material_icon_name="published_with_changes", background_color="#d9d9d9"))
class ConvertXmlToJson(Task):
    input_specs = InputSpecs({'input_file':  InputSpec(File)})
    output_specs = OutputSpecs({'output_json_file': OutputSpec(File)})
    config_specs = ConfigSpecs({})

    script_convert = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "_convert_xml_to_json.py")

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        input_file: File = inputs['input_file']
        file_path = input_file.path

        shell_proxy = CobraEnvHelper.create_proxy(self.message_dispatcher)

        output_path = os.path.join(shell_proxy.working_dir, "model.json")
        shell_proxy.run(
            f"python3 {self.script_convert} {file_path} {output_path}", shell_mode=True)

        json_file = File(output_path)

        return {'output_json_file': json_file}
