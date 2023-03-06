# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import networkx as nx
from gws_core import (BadRequestException, BoolParam, ConfigParams, InputSpec,
                      OutputSpec, ResourceSet, StrParam, Table, Task,
                      TaskInputs, TaskOutputs, TechnicalInfo,
                      resource_decorator, task_decorator)
from pandas import DataFrame

from ...data.entity_id_table import EntityIDTable
from ...network.graph.graph import Graph
from ...network.network import Network
from .helper.isolate_finder_helper import IsolateFinderHelper
from .isolate_finder_result import IsolateFinderResult


@task_decorator("IsolateFinder", human_name="Isolate finder",
                short_description="Finds genes/reactions that are isolates, i.e. topologically non-connected to the cell growth")
class IsolateFinder(Task):
    """
    IsolateFinder.

    Finds wether genes/reactions are isolates, i.e. topologically non-connected to the cell growth
    """

    input_specs = {'network': InputSpec(Network)}
    output_specs = {'result': OutputSpec(IsolateFinderResult)}
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        network: Network = inputs["network"]
        helper = IsolateFinderHelper()
        helper.attach_task(self)
        comp_table, rxn_table = helper.find_isolates(network)

        result = IsolateFinderResult()
        result.set_compound_table(comp_table)
        result.set_reaction_table(rxn_table)
        return {"result": result}
