from gws_core import (ConfigParams, InputSpec, OutputSpec, File,
                      Task, TaskInputs, TaskOutputs, task_decorator, BadRequestException)

from cobra.io import save_json_model, read_sbml_model, load_matlab_model


@task_decorator("ConvertXmlToJson", human_name="XML/Matlab to JSON",
                short_description="This task converts a xml file or a matlab file into a json file")
class ConvertXmlToJson(Task):
    input_specs = {'input_file':  InputSpec(File)}
    output_specs = {'output_json_file': OutputSpec(File)}
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        input_file: File = inputs['input_file']
        file_path = input_file.path

        if file_path.endswith('.xml'):
            model = read_sbml_model(input_file)
        elif file_path.endswith('.mat'):
            model = load_matlab_model(file_path)
        else:
            raise BadRequestException("Your file need to have a extension '.xml' or '.mat'")

        save_json_model(model, "model.json")
        json_file = File("model.json")

        return {'output_json_file': json_file}
