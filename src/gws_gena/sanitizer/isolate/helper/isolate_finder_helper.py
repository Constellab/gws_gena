
from typing import Tuple

import networkx as nx
from gws_core import BadRequestException, Table
from pandas import DataFrame

from ....helper.base_helper import BaseHelper
from ....network.graph.graph import Graph
from ....network.network import Network

class IsolateFinderHelper(BaseHelper):

    """ IsolateFinderHelper """

    def find_isolates(self, network: Network) -> Tuple[Table, Table]:
        graph = Graph(network=network)
        nxgraph = graph.get_nx_graph()

        biomass = network.get_biomass_compound()
        if biomass is None:
            raise BadRequestException("No biomass defined")

        # compound table
        comp_data = []
        rxn_ids = []
        for comp in network.compounds.values():
            has_path = nx.has_path(nxgraph, comp.id, biomass.id)
            if has_path:
                continue
            comp_data.append([comp.id, comp.chebi_id, comp.name])
            for edge in nxgraph.edges(comp.id):
                rxn_id = nxgraph.get_edge_data(*edge)["rxn_id"]
                if rxn_id not in rxn_ids:
                    rxn_ids.append(rxn_id)

        comp_data = DataFrame(comp_data, columns=["id", "chebi_id", "name"])
        comp_table = Table(comp_data)

        # reaction table
        rxn_data = []
        for rxn_id in rxn_ids:
            rxn = network.get_reaction_by_id(rxn_id)
            rxn_data.append([rxn.id, rxn.rhea_id, rxn.name])
        rxn_data = DataFrame(rxn_data, columns=["id", "rhea_id", "name"])
        rxn_table = Table(rxn_data)

        return comp_table, rxn_table
