
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


@task_decorator("TransformerEntityIDTable", human_name="Transformer Entity ID Table",
                short_description="Task to transform table into Entity ID",
                style=TypingStyle.material_icon(material_icon_name="change_circle", background_color="#d9d9d9"))
class TransformerEntityIDTable(Task):
    """
    TransformerEntityIDTable class

    Allows to transform a Table with the right columns names to create an Entity ID Table.

    An Entity ID Table is a table of entity IDs (CheBI IDs, Rhea IDs, EC Numbers, User-defined IDs, ...)

    * The first column the ID of the entity (official or user-defined ID) `[required]`
    * The next columns are optional [OPTIONAL]

    Your File must have at least:
    - a column with the ID of the entity
    For example:

    | id           |  name                  |
    | -------------|------------------------|
    | CHEBI:57972  |  L-alanine             |

    """

    id_column: str = "entity_id"

    input_specs = InputSpecs({
        'table': InputSpec(Table, human_name="Initial table", optional=False)})
    output_specs = OutputSpecs({'transformed_table': OutputSpec(Table)})
    config_specs: ConfigSpecs = ConfigSpecs({
        'id_column_name':
        StrParam(
            default_value=id_column, human_name="Entity ID column name",
            short_description="The name of the Entity ID column")})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        table = inputs["table"]

        name_entity_id_column = params["id_column_name"]

        if not table.column_exists(name_entity_id_column):
            raise Exception(
                f"Cannot import Table. No entity ID found (no column with name '{name_entity_id_column}')")

        # If the column names are incorrect, rename them.
        if name_entity_id_column != self.id_column:
            table.set_column_name(
                current_name=name_entity_id_column, new_name=self.id_column)

        # Test if the list is not empty
        ids = table.get_column_data(self.id_column)
        if len(ids) == 0:
            raise Exception(
                "Cannot import the table. The list of ids is empty.")

        # Test if there is no duplicates
        unique_ids = list(set(ids))
        if len(ids) > len(unique_ids):
            duplicates = [elt for elt in ids if elt not in unique_ids]
            raise Exception(
                f"Cannot import the table. The ids in the table must be unique. Duplicates are {duplicates}.")

        return {"transformed_table": table}
