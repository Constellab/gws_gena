from gws_core import (
    ConfigParams,
    ConfigSpecs,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    StrParam,
    Table,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingStyle,
    task_decorator,
)


@task_decorator(
    "TransformerFluxTable",
    human_name="Transformer Flux Table",
    short_description="Task to transform table into Flux table",
    style=TypingStyle.material_icon(material_icon_name="change_circle", background_color="#d9d9d9"),
)
class TransformerFluxTable(Task):
    """
    TransformerFluxTable class

    Allows to transform a Table with the right columns names to create a Flux Table.
    The `Flux Table` is a generic table of entity IDs (CheBI IDs, Rhea IDs, EC Numbers, User-defined IDs, ...).
    It's a table of experimentally measured (or user-defined) metabolic fluxes

    The header of you Table can be the following: "reaction_id,target,lower_bound,upper_bound,confidence_score"

    * The first column is the list of `reaction ids` and/or `ec numbers` `[required]`. They uniquely identify each reaction of a network.
    * The next columns are:
      * target: the value of the flux measured experimentally (e.g. `mol/gDW/h`) `[required]`
      * upper_bound: the upper bound of the flux (e.g. `mol/gDW/h`) `[required]`
      * lower_bound: the lower bound of the flux (e.g. `mol/gDW/h`) `[required]`
      * confidence_score: the confidence score of the flux `[required]`

    For example:

    | id                      | target    | lower_bound  | lower_bound  | confidence_score   |
    | ------------------------|-----------|--------------|--------------|--------------------|
    | RHEA_62620_1_11_1_24    | 0.234     | 0            | 1000         | 1.0                |
    | 6.3.1.2                 | -1.234    | -5           | 0            | 1.0                |

    This Task manages multiple simulations. So if you have different values of target,lower_bound,upper_bound; set them as a list like this:
    reaction_id,target,lower_bound,upper_bound,confidence_score
    reaction1,"[0.04,  0.045,  0.035]","[0.01, 0.008, -0.02]","[0.03, -0.003, 0.001]","[1, 1, 1]"
    """

    entity_id_column_name: str = "id"
    target_column_name: str = "target"
    lower_bound_column_name: str = "lower_bound"
    upper_bound_column_name: str = "upper_bound"
    confidence_score_column: str = "confidence_score"

    input_specs = InputSpecs(
        {"table": InputSpec(Table, human_name="Initial table", optional=False)}
    )
    output_specs = OutputSpecs({"transformed_table": OutputSpec(Table)})
    config_specs: ConfigSpecs = ConfigSpecs(
        {
            "entity_id_column": StrParam(
                default_value=entity_id_column_name,
                human_name="Entity column name",
                short_description="The name of the column of entity ids",
            ),
            "target_column": StrParam(
                default_value=target_column_name,
                human_name="Target column name",
                short_description="The name of the target column",
            ),
            "lower_bound_column": StrParam(
                default_value=lower_bound_column_name,
                human_name="Lower bound column name",
                short_description="The name of the lower-bound column",
            ),
            "upper_bound_column": StrParam(
                default_value=upper_bound_column_name,
                human_name="Upper bound column name",
                short_description="The name of the upper-bound column",
            ),
            "confidence_score_column": StrParam(
                default_value=confidence_score_column,
                human_name="Confidence score column name",
                short_description="The name of the confidence score column",
            ),
        }
    )

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
                current_name=name_entity_id_column, new_name=self.entity_id_column_name
            )
        if name_target_column != self.target_column_name:
            table.set_column_name(current_name=name_target_column, new_name=self.target_column_name)
        if name_lower_bound_column != self.lower_bound_column_name:
            table.set_column_name(
                current_name=name_lower_bound_column, new_name=self.lower_bound_column_name
            )
        if name_upper_bound_column != self.upper_bound_column_name:
            table.set_column_name(
                current_name=name_upper_bound_column, new_name=self.upper_bound_column_name
            )
        if name_confidence_score_column != self.confidence_score_column:
            table.set_column_name(
                current_name=name_confidence_score_column, new_name=self.confidence_score_column
            )

        return {"transformed_table": table}
