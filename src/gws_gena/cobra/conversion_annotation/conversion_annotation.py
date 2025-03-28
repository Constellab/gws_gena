import os

import pandas as pd
from gws_core import (ConfigParams, File, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, StrParam, Table, Task, TaskInputs, ConfigSpecs,
                      TaskOutputs, task_decorator, TaskRunner, TypingStyle)
from .create_database_task import TransformMetabolitesFile, TransformReactionsFile

from ..cobra_env import CobraEnvHelper


@task_decorator("ConvertAnnotation", human_name="Convert Model Annotation",
                short_description="This task adds metabolites and reactions identifiers (ChEBI, Rhea and ec-number) to a model",
                style=TypingStyle.material_icon(material_icon_name="hub", background_color="#d9d9d9"))
class ConvertAnnotation(Task):
    """
    Convert annotation task class

    Complete the annotation of a metabolic model thanks to internal correspondence tables.
    This task can add missing identifiers to metabolics and reactions. For metabolites, it adds ChEBI identifiers. For reactions, it can add Rhea identifiers and EC numbers.

    Please provide your metabolic model in input. In output, you will get your model updated and a table summarising the changes made.

    """
    input_specs = InputSpecs({'input_model':  InputSpec(
        File, human_name="Model", short_description="The model to annotate")})
    output_specs = OutputSpecs({
        'output_model_annotated': OutputSpec(File, human_name="Model annotated", short_description="The model completed"),
        'output_results': OutputSpec(Table, human_name="Results Annotation", short_description="The annotation result table")})
    config_specs = ConfigSpecs({
        "metabolites_id":
        StrParam(
            allowed_values=["", "BiGG", "Literal_name", "Other"],
            default_value=None, optional=False, human_name="Metabolite ID",
            short_description="What is the type of metabolite 'id'?"),
        "metabolites_name":
        StrParam(
            allowed_values=["", "BiGG", "Literal_name", "Other"],
            default_value=None, optional=False, human_name="Metabolite name",
            short_description="What is the type of metabolite 'name'?"),
        "reaction_id":
        StrParam(
            allowed_values=["", "BiGG", "Other"],
            default_value=None, optional=False, human_name="Reaction ID",
            short_description="What is the type of reaction 'id'?"),
        "reaction_name":
        StrParam(
            allowed_values=["", "BiGG", "Other"],
            default_value=None, optional=False, human_name="Reaction name",
            short_description="What is the type of reaction 'name'?")})

    script_conversion_annotation = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                                "_conversion_annotation.py")

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        input_model: File = inputs['input_model']

        metabolites_id = params["metabolites_id"]
        metabolites_name = params["metabolites_name"]
        reaction_id = params["reaction_id"]
        reaction_name = params["reaction_name"]

        # TransformMetabolitesFile
        runner_transform_metabolites_file = TaskRunner(
            task_type=TransformMetabolitesFile)
        # execute the TaskRunner
        outputs_transform_metabolites_file = runner_transform_metabolites_file.run()
        # check if we retrieve the output
        path_metabolites = outputs_transform_metabolites_file['output'].list_dir_path(
        )
        for path in path_metabolites:
            if path.endswith('restructured_metabolites_file.txt'):
                db_metabolites_path = path
                break

        # TransformReactionsFile
        runner_transform_reactions_file = TaskRunner(
            task_type=TransformReactionsFile)
        # execute the TaskRunner
        outputs_transform_reactions_file = runner_transform_reactions_file.run()
        # check if we retrieve the output
        path_reactions = outputs_transform_reactions_file['output'].list_dir_path(
        )
        for path in path_reactions:
            if path.endswith('restructured_reactions_file.txt'):
                db_reactions_path = path
                break

        shell_proxy = CobraEnvHelper.create_proxy(self.message_dispatcher)

        output_path = os.path.join(
            shell_proxy.working_dir, "model_annotated.json")
        results_path = os.path.join(shell_proxy.working_dir, "results.csv")

        shell_proxy.run(
            f"python3 {self.script_conversion_annotation} {input_model.path} {output_path} {metabolites_id} {metabolites_name} {reaction_id} {reaction_name} {results_path} {db_metabolites_path} {db_reactions_path}",
            shell_mode=True)

        model_annotated = File(output_path)
        results_csv = pd.read_csv(results_path)
        results_csv = results_csv.drop(columns=["Unnamed: 0"])
        results_table = Table(results_csv)

        return {'output_model_annotated': model_annotated,
                'output_results': results_table}
