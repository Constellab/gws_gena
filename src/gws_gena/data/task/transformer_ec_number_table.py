
from gws_core import (ConfigParams, ConfigSpecs, Task,
                      StrParam, Table, TypingStyle,
                      task_decorator, InputSpecs, InputSpec, OutputSpec, OutputSpecs, TaskInputs, TaskOutputs)

@task_decorator("TransformerECNumberTable", human_name="Transformer EC Number Table",
                    short_description="Task to transform table into EC Number",
                    style=TypingStyle.material_icon(material_icon_name="change_circle", background_color="#d9d9d9"))
class TransformerECNumberTable(Task):
    """
    TransformerECNumber class

    Allows to transform a Table with the right columns names to create a EC Number Table.
    The `EC Table` is a table of EC numbers.

    Your File must have at least a column with the ec-number and can contains a column with the compound name.

    For example:
    | component           | ec_number |
    |---------------------|-----------|
    | PNEG_00964          | 1.4.1.2   |
    | PNEG_02355          | 4.2.1.10  |
    """

    ec_number_name: str = "ec_number"

    input_specs = InputSpecs({
        'table': InputSpec(Table, human_name="Initial table", is_optional=False)})
    output_specs = OutputSpecs({'transformed_table': OutputSpec(Table)})
    config_specs: ConfigSpecs = {
        'ec_number_column':
        StrParam(
            default_value=ec_number_name, human_name="EC number column name",
            short_description="The name of the EC number column")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        table = inputs["table"]

        name_ec_number_column = params["ec_number_column"]

        if not table.column_exists(name_ec_number_column):
            raise Exception(f"Cannot import Table. No ec numbers found (no column with name '{name_ec_number_column}')")

        #If the column names are incorrect, rename them.
        if name_ec_number_column != self.ec_number_name:
            table.set_column_name(current_name = name_ec_number_column,new_name = self.ec_number_name)

        # clean ec data
        table._data.replace(
            to_replace={self.ec_number_name: r"EC:"},
            value={self.ec_number_name: ""},
            regex=True,
            inplace=True)


        return {"transformed_table": table}
