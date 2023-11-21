# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ..data.flux_table import FluxTable
from ..network.network import Network
from .context import Context
from .helper.context_builder_helper import ContextBuilderHelper


@task_decorator("ContextBuilder", human_name="Context builder",
                short_description="Build a context for a metabolic network using a flux table")
class ContextBuilder(Task):
    """
    ContextBuilder Task

    This task creates a `Context` object using a `FluxTable` and metabolic `Network`.
    A `Context` object is used to create digital twins and perform metabolic flux analyses.

    - The `FluxTable` gives a list of metabolic fluxes experimentally measured.
    It generally corresponds to the consupmtion or production rates of a list on metabolites measured in a bioreactor.
    - The `Network` is a metabolic network
    """

    input_specs = InputSpecs({'network': InputSpec(Network), 'flux_table': InputSpec(FluxTable)})
    output_specs = OutputSpecs({'context': OutputSpec(Context)})
    config_specs = {}

    def run(self, _: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        flux: FluxTable = inputs["flux_table"]
        net: Network = inputs["network"]

        helper = ContextBuilderHelper()
        helper.attach_task(self)
        ctx = helper.build(net, flux)

        return {"context": ctx}
