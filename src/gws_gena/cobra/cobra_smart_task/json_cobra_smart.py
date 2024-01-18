# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.config_params import ConfigParams

from typing import Any, Dict, List

from gws_core.impl.openai.open_ai_helper import OpenAiHelper
from gws_core.impl.openai.smart_task_base import SmartTaskBase
from gws_core.impl.file.file import File
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs

from gws_gena.gena.utils.gws_gena_packages import GwsGenaPackages


import cobra


@task_decorator("SmartCobra", human_name="Smart json modificator (cobra)",
                short_description="Generate an json model with modifications asked.")
class SmartCobra(SmartTaskBase):
    """
This task is still in beta version.

This task uses openAI API to generate python code that modify a genome scale metabolic model stored in a json format; using cobra library. This code is then automatically executed.

Here are few examples of what you can ask for:
Please change the id of the metabolite "xxx" by "yyy"
Please change the id of the reaction "xxx" by "yyy"
Please change the id of the gene "xxx" by "yyy" with the function cobra.manipulation.modify.rename_genes

The data of the model is not transferered to OpenAI, only the provided text.
    """

    input_specs: InputSpecs = InputSpecs({
        'source': InputSpec(File),
    })
    output_specs: OutputSpecs = OutputSpecs({
        'target': OutputSpec(File, human_name='Model Modified', short_description='Model modified.')
    })

    def build_main_context(self, params: ConfigParams, task_inputs: TaskInputs,code_inputs: Dict[str, Any]) -> str:
        # prepare the input

        return f"""{self.VAR_PY_INTRO}
                The code purpose is to modify a genome-scale metabolic model, stored as a JSON file, using the Cobra package.
                {self.VAR_INPUTS}
                {self.VAR_OUTPUTS}
                {self.VAR_CODE_RULES}"""

    def build_code_inputs(self, params: ConfigParams, task_inputs: TaskInputs) -> dict:
        # get the model
        model: File = task_inputs["source"]

        # Load the model from JSON file
        model_cobra = cobra.io.load_json_model(model.path)

        return {"source": model_cobra}

    def get_code_expected_output_types(self) -> Dict[str, Any]:
        return {"target": cobra.core.model.Model}

    def get_available_package_names(self) -> List[str]:
        return [GwsGenaPackages.COBRA]

    def build_task_outputs(self, params: ConfigParams, task_inputs: TaskInputs,
                           code_outputs: dict, generated_code: str) -> dict:
        target = code_outputs.get("target", None)

        if target is None:
            raise Exception("The code did not generate any output")

        if not isinstance(target, cobra.core.model.Model):
            raise Exception("The output must be a Cobra model")

        # Save the modified model to a new JSON file
        cobra.io.save_json_model(target, "modified_model.json")

        model_modified = File("modified_model.json")

        return {'target': model_modified}
