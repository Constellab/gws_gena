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
    "TransformerBiomassReactionTable",
    human_name="Transformer Biomass Reaction",
    short_description="Task to transform table into Biomass Reaction table",
    style=TypingStyle.material_icon(material_icon_name="change_circle", background_color="#d9d9d9"),
)
class TransformerBiomassReactionTable(Task):
    """
    TransformerBiomassReactionTable class

    Allows to transform a Table with the right columns names to create a Biomass Reaction Table.
    The `Biomass Reaction Table` is a stoichiometry table describing the composition of a cell (or organism) biomass.


    A stoichiometry resource table describing the composition of the biomass.

    * The first column is the compound name (offical or user-defined name) `[required]`
    * The next columns are:
      * chebi_id: the chebi ids of componds of they are known (each chebi id must be prefixed by the keyword CHEBI:). `[required]`
      * biomass: the biomass reaction data (described like a stoichiometric matrix) `[required]`
      * other colums: these columns describe the reaction of the intermediate biomass constituents (described like a stoichiometric matrix) `[optional]`

    For example:

    | component               | chebi_id    | biomass      | protein |
    |-------------------------|-------------|--------------|---------|
    | biomass                 |             | 1            |         |
    | protein                 |             | -0.3176      | 1       |
    | DNA                     |             | -0.0503      |         |
    | RNA                     |             | -0.0259      |         |
    | Cofactors               |             | -0.0216      |         |
    | Cell wall               |             | -0.115       |         |
    | Carbohydrates           |             | -0.2021      |         |
    | Phospholipids           |             | -0.1542      |         |
    | L-alanine zwitterion    | CHEBI:57972 |              | -0.5875 |
    | L-argininium(1+)        | CHEBI:32682 |              | -0.1040 |
    | L-asparagine zwitterion | CHEBI:58048 |              | -0.4755 |
    | L-aspartate(1-)         | CHEBI:29991 |              | -0.6109 |
    | L-cysteine zwitterion   | CHEBI:35235 |              | -0.4755 |
    """

    chebi_id_column_name: str = "chebi_id"
    biomass_column_name: str = "biomass"
    entity_column_name: str = "entity"

    input_specs = InputSpecs(
        {"table": InputSpec(Table, human_name="Initial table", optional=False)}
    )
    output_specs = OutputSpecs({"transformed_table": OutputSpec(Table)})
    config_specs: ConfigSpecs = ConfigSpecs(
        {
            "entity_column": StrParam(
                default_value=entity_column_name,
                human_name="Entity column name",
                short_description="The name of the entity column",
            ),
            "chebi_id_column": StrParam(
                default_value=chebi_id_column_name,
                human_name="ChEBI ID column name",
                short_description="The name of the column of ChEBI ID",
            ),
            "biomass_column": StrParam(
                default_value=biomass_column_name,
                human_name="Biomass column name",
                short_description="The name of the biomass column",
            ),
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        table = inputs["table"]

        name_entity_column = params["entity_column"]
        name_chebi_id_column = params["chebi_id_column"]
        name_biomass_column = params["biomass_column"]

        if not table.column_exists(name_entity_column):
            raise Exception(
                f"Cannot import BiomassReactionTable.  No entity column found (no column with name '{name_entity_column}')"
            )
        if not table.column_exists(name_chebi_id_column):
            raise Exception(
                f"Cannot import BiomassReactionTable. No CheBI ID column found (no column with name '{name_chebi_id_column}')"
            )
        if not table.column_exists(name_biomass_column):
            raise Exception(
                f"Cannot import BiomassReactionTable.  No biomass equation found (no column with name '{name_biomass_column}')"
            )

        # If the column names are incorrect, rename them.
        if name_entity_column != self.entity_column_name:
            table.set_column_name(current_name=name_entity_column, new_name=self.entity_column_name)
        if name_chebi_id_column != self.chebi_id_column_name:
            table.set_column_name(
                current_name=name_chebi_id_column, new_name=self.chebi_id_column_name
            )
        if name_biomass_column != self.biomass_column_name:
            table.set_column_name(
                current_name=name_biomass_column, new_name=self.biomass_column_name
            )

        return {"transformed_table": table}
