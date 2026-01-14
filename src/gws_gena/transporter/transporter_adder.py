from gws_core import (
    ConfigParams,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    Table,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingStyle,
    task_decorator,
)

from ..data.task.transformer_medium_table import TransformerMediumTable
from ..network.network import Network
from ..recon.helper.recon_helper import ReconHelper


@task_decorator(
    "TransporterAdder",
    human_name="Transporter adder",
    short_description="Transporter adder",
    style=TypingStyle.material_icon(material_icon_name="playlist_add", background_color="#d9d9d9"),
)
class TransporterAdder(Task):
    """
    Transporter adder task.

    This task involves adding compounds to an existing network. This can be used to add the medium compounds.

    The task will add medium compounds to a network and also create associated medium reactions.

    In input, provide your network and a Medium table (with the name and ChEBI ID of your metabolites).
    In output you will get your extended network.

    """

    input_specs = InputSpecs(
        {
            "network": InputSpec(Network, human_name="The network"),
            "medium_table": InputSpec(Table, human_name="Medium table"),
        }
    )
    output_specs = OutputSpecs({"network": OutputSpec(Network)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        helper = ReconHelper()
        helper.attach_message_dispatcher(self.message_dispatcher)

        net = inputs["network"]
        medium_table = inputs["medium_table"]

        entity_column_name = TransformerMediumTable.entity_column_name
        if not medium_table.column_exists(entity_column_name):
            raise Exception(
                f"Cannot import Medium Table: no column with name '{entity_column_name}' use the Transformer Medium Table"
            )
        chebi_id_column_name = TransformerMediumTable.chebi_id_column_name
        if not medium_table.column_exists(chebi_id_column_name):
            raise Exception(
                f"Cannot import Medium Table: no column with name '{chebi_id_column_name}' use the Transformer Medium Table"
            )

        helper.add_medium_to_network(net, medium_table)

        return {"network": net}
