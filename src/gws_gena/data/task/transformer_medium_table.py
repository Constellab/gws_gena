
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


@task_decorator("TransformerMediumTable", human_name="Transformer Medium",
                short_description="Task to transform table into Medium table",
                style=TypingStyle.material_icon(material_icon_name="change_circle", background_color="#d9d9d9"))
class TransformerMediumTable(Task):
    """
    TransformerMediumTable class

    Allows to transform a Table with the right columns names to create a Medium Table.
    The `Medium Table` is a table representing a culture medium composition.

    * The first column is the compound name (offical or user-defined name) `[required]`
    * The next column is the list chebi ids `[required]`

    For example:

    | entity              | chebi_id     |
    | --------------------|--------------|
    | 2-oxoglutarate      | CHEBI:16810  |
    | glutamine           | CHEBI:18050  |

    """

    chebi_id_column_name: str = "chebi_id"
    entity_column_name: str = "entity"

    input_specs = InputSpecs({
        'table': InputSpec(Table, human_name="Initial table", optional=False)})
    output_specs = OutputSpecs({'transformed_table': OutputSpec(Table)})
    config_specs: ConfigSpecs = ConfigSpecs({
        'entity_column':
        StrParam(
            default_value=entity_column_name, human_name="Entity column name",
            short_description="The name of the entity column"),
        'chebi_id_column':
        StrParam(
            default_value=chebi_id_column_name, human_name="ChEBI ID column name",
            short_description="The name of the column of ChEBI ID")})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        table = inputs["table"]

        name_entity_column = params["entity_column"]
        name_chebi_id_column = params["chebi_id_column"]

        if not table.column_exists(name_entity_column):
            raise Exception(
                f"Cannot import BiomassReactionTable.  No entity column found (no column with name '{name_entity_column}')")
        if not table.column_exists(name_chebi_id_column):
            raise Exception(
                f"Cannot import BiomassReactionTable. No CheBI ID column found (no column with name '{name_chebi_id_column}')")

        # If the column names are incorrect, rename them.
        if name_entity_column != self.entity_column_name:
            table.set_column_name(
                current_name=name_entity_column, new_name=self.entity_column_name)
        if name_chebi_id_column != self.chebi_id_column_name:
            table.set_column_name(
                current_name=name_chebi_id_column, new_name=self.chebi_id_column_name)

        return {"transformed_table": table}
