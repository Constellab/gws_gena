
from gws_core import (ConfigParams, ConfigSpecs, Task,
                      StrParam, Table, TypingStyle,
                      task_decorator, InputSpecs, InputSpec, OutputSpec, OutputSpecs, TaskInputs, TaskOutputs)


@task_decorator("TransformerPhenotypeTable", human_name="Transformer Phenotype Table",
                short_description="Task to transform table into Phenotype table",
                style=TypingStyle.material_icon(material_icon_name="change_circle", background_color="#d9d9d9"))
class TransformerPhenotypeTable(Task):
    """
    TransformerPhenotypeTable class

    Allows to transform a Table with the right columns names to create a Phenotype Table.
    The Phenotype Table is a generic table of entity IDs (CheBI IDs, Rhea IDs, EC Numbers, User-defined IDs, ...).


    The phenotype table is similar to the flux table but the fluxes are related to
    entities (metabolite, biomass) instead of reactions. Qualitative observations are described by
    upper and lower bound only.

    * The first column is the list of `entity ids`. They uniquely identify each reaction of a network.
    * The next columns are:
      * target: the value of the flux measured experimentally (e.g. `mol/L/h`) `[required]`
      * upper_bound: the upper bound of the flux (e.g. `mol/L/h`) `[required]`
      * lower_bound: the lower bound of the flux (e.g. `mol/L/h`) `[required]`
      * confidence_score: the confidence score of the flux `[required]`
      * ... : other optional columns

    For example:

    | id                  | target    | lower_bound  | upper_bound  | confidence_score   | chebi_id     |
    | --------------------|-----------|--------------|--------------|--------------------|--------------|
    | biomass             |           | 0            | 1000         | 1.0                | biomass      |
    | 2-oxoglutarate      |           | 0            | 1000         | 1.0                | CHEBI:16810  |
    | glutamine           | 1.23      | 0            | 2.0          | 1.0                | CHEBI:18050  |

    This Task manages multiple simulations. So if you have different values of target,lower_bound,upper_bound; set them as a list like this:
    id,target,lower_bound,upper_bound,confidence_score,chebi_id
    id1,"[0.04,  0.045,  0.035]","[0.01, 0.008, -0.02]","[0.03, -0.003, 0.001]","[1, 1, 1]",CHEBI
    """

    entity_id_column_name: str = "id"
    target_column_name: str = "target"
    lower_bound_column_name: str = "lower_bound"
    upper_bound_column_name: str = "upper_bound"
    confidence_score_column: str = "confidence_score"

    input_specs = InputSpecs({
        'table': InputSpec(Table, human_name="Initial table", is_optional=False)})
    output_specs = OutputSpecs({'transformed_table': OutputSpec(Table)})
    config_specs: ConfigSpecs = ConfigSpecs({
        'entity_id_column':
        StrParam(
            default_value=entity_id_column_name, human_name="Entity column name",
            short_description="The name of the column of entity ids"),
        'target_column':
        StrParam(
            default_value=target_column_name, human_name="Target column name",
            short_description="The name of the target column"),
        'lower_bound_column':
        StrParam(
            default_value=lower_bound_column_name, human_name="Lower bound column name",
            short_description="The name of the lower-bound column"),
        'upper_bound_column':
        StrParam(
            default_value=upper_bound_column_name, human_name="Upper bound column name",
            short_description="The name of the upper-bound column"),
        'confidence_score_column':
        StrParam(
            default_value=confidence_score_column, human_name="Confidence score column name",
            short_description="The name of the confidence score column")})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        table = inputs["table"]

        name_entity_id_column = params["entity_id_column"]
        name_target_column = params["target_column"]
        name_lower_bound_column = params["lower_bound_column"]
        name_upper_bound_column = params["upper_bound_column"]
        name_confidence_score_column = params["confidence_score_column"]

        # If the column names are incorrect, rename them.
        if name_entity_id_column != self.entity_id_column_name:
            # rename column
            table.set_column_name(
                current_name=name_entity_id_column, new_name=self.entity_id_column_name)
        if name_target_column != self.target_column_name:
            table.set_column_name(
                current_name=name_target_column, new_name=self.target_column_name)
        if name_lower_bound_column != self.lower_bound_column_name:
            table.set_column_name(
                current_name=name_lower_bound_column, new_name=self.lower_bound_column_name)
        if name_upper_bound_column != self.upper_bound_column_name:
            table.set_column_name(
                current_name=name_upper_bound_column, new_name=self.upper_bound_column_name)
        if name_confidence_score_column != self.confidence_score_column:
            table.set_column_name(
                current_name=name_confidence_score_column, new_name=self.confidence_score_column)

        return {"transformed_table": table}
