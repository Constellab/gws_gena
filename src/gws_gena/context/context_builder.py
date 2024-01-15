# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math

from gws_core import (BadRequestException, ConfigParams, InputSpec, OutputSpec,
                      Task, TaskInputs, TaskOutputs, task_decorator)

from ..data.flux_table import FluxTable
from ..data.phenotype_table import PhenotypeTable
from ..network.network import Network
from ..network.reaction.reaction import Reaction
from .context import Context
from .measure import Measure
from .typing.measure_typing import MeasureDict
from .typing.variable_typing import VariableDict
from .variable import Variable
from .helper.context_builder_helper import ContextBuilderHelper


@task_decorator("ContextBuilder", human_name="Context builder",
                short_description="Build a context for a metabolic network using a flux table")
class ContextBuilder(Task):
    """
    ContextBuilder Task

    This task creates a `Context` object using a `FluxTable` and metabolic `Network`.
    A `Context` object is used to create digital twins and perform metabolic flux analyses.

    - Inputs
      - The `Network` is a metabolic network
      - The `Flux Table` gives the list of metabolic fluxes that are experimentally measured.
      - The `Phenotype table` gives the list of internal metabolic variations that are experimentally measured.
    - Output
      - The `Context` object that can be used for flux simulation
    It generally corresponds to the consupmtion or production rates of a list on metabolites measured in a bioreactor.

    """

    input_specs = {
        'network': InputSpec(Network),
        'flux_table': InputSpec(FluxTable, human_name="Flux table", is_optional=True),
        'pheno_table': InputSpec(PhenotypeTable, human_name="Phenotype table", is_optional=True)}
    output_specs = {'context': OutputSpec(Context)}
    config_specs = {}

    def run(self, _: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        flux_table: FluxTable = inputs.get("flux_table")
        pheno_table: PhenotypeTable = inputs.get("pheno_table")

        net: Network = inputs["network"]
        helper = ContextBuilderHelper()
        helper.attach_task(self)
        ctx = helper.build(net, flux_table, pheno_table)

        return {"context": ctx}
