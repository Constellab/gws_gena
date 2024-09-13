
from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, Table, Task, TaskInputs, TaskOutputs,
                      TypingStyle, task_decorator)

from gws_gena.network.network_cobra import NetworkCobra
from .context import Context
from .helper.context_builder_helper_v2 import ContextBuilderHelperV2

@task_decorator("ContextBuilderV2", human_name="Context builder V2",
                short_description="Build a context for a metabolic network using a flux table",
                style=TypingStyle.material_icon(material_icon_name="build", background_color="#d9d9d9"))
class ContextBuilderV2(Task):
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

    input_specs = InputSpecs({
        'network': InputSpec(NetworkCobra),
        'flux_table': InputSpec(Table, human_name="Flux table", is_optional=True),
        'pheno_table': InputSpec(Table, human_name="Phenotype table", is_optional=True)})
    output_specs = OutputSpecs({'context': OutputSpec(Context)})

    def run(self, _: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        flux_table: Table = inputs.get("flux_table")
        pheno_table: Table = inputs.get("pheno_table")

        net: NetworkCobra = inputs["network"]
        helper = ContextBuilderHelperV2()
        helper.attach_message_dispatcher(self.message_dispatcher)
        ctx = helper.build(net, flux_table, pheno_table)

        return {"context": ctx}
