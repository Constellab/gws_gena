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

from ..network.network import Network
from .context import Context
from .helper.context_builder_helper import ContextBuilderHelper


@task_decorator(
    "ContextBuilder",
    human_name="Context builder",
    short_description="Build a context for a metabolic network using a flux table",
    style=TypingStyle.material_icon(material_icon_name="build", background_color="#d9d9d9"),
)
class ContextBuilder(Task):
    """
    ContextBuilder Task

    This task creates a `Context` object using a `Flux Table` or a 'Phenotype Table' and a metabolic `Network`.
    A `Context` object is used to create digital twins and perform metabolic flux analyses.

    - Inputs
      - The `Network` is a metabolic network
      - The `Flux Table` gives the list of metabolic fluxes that are experimentally measured.
      - The `Phenotype table` gives the list of internal metabolic variations that are experimentally measured.
    - Output
      - The `Context` object that can be used for flux simulation
    It generally corresponds to the consumption or production rates of a list on metabolites measured in a bioreactor.

    """

    input_specs = InputSpecs(
        {
            "network": InputSpec(Network),
            "flux_table": InputSpec(Table, human_name="Flux table", optional=True),
            "pheno_table": InputSpec(Table, human_name="Phenotype table", optional=True),
        }
    )
    output_specs = OutputSpecs({"context": OutputSpec(Context)})

    def run(self, _: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        flux_table: Table = inputs["flux_table"]
        pheno_table: Table = inputs["pheno_table"]

        net: Network = inputs["network"]
        helper = ContextBuilderHelper()
        helper.attach_message_dispatcher(self.message_dispatcher)
        ctx = helper.build(net, flux_table, pheno_table)

        return {"context": ctx}
