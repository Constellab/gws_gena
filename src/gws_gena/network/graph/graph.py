# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

import networkx as nx
from gws_biota import Cofactor as BiotaCofactor
from gws_biota.unicell.unicell_service import UnicellService as BiotaUnicellService


class Graph:
    _nxgraph = None
    _rhea_edge_map: Dict[str, List[str]] = None

    def __init__(self, network: 'Network' = None):
        if network is None:
            self._graph = nx.Graph()
            self._rhea_edge_map = {}
        else:
            (nxgraph, rhea_edge_map) = self._create_nxgraph_from_network(network)
            self._nxgraph = nxgraph
            self._rhea_edge_map = rhea_edge_map

    def gap_fill(self, from_graph=None, tax_id=None, weight=None, partial=False):
        """ Finds set of edges to gap-fill  graph """
        if from_graph:
            avail = from_graph.edges()
        else:
            unicell = BiotaUnicellService.create_unicell(tax_id=tax_id)
            avail = unicell.get_graph().edges()

        return nx.k_edge_augmentation(self._nxgraph, k=1, avail=avail, weight=weight, partial=partial)

    # def edge_disjoint_paths(self, source, target, flow_func=None, cutoff=None, auxiliary=None, residual=None):
    #     pass

    @classmethod
    def _create_nxgraph_from_network(cls, network: 'Network'):
        """ Construct a `Graph` from a `Network` """

        nxgraph = nx.Graph()
        rhea_edge_map = {}

        cofactor_list: List[str] = BiotaCofactor.get_factors_as_list()
        for rxn in network.reactions.get_elements().values():
            for comp1 in rxn.substrates.values():
                chebi_id_1 = comp1.chebi_id
                if chebi_id_1 in cofactor_list:
                    continue
                for comp2 in rxn.products.values():
                    chebi_id_2 = comp2.chebi_id
                    if chebi_id_2 in cofactor_list:
                        continue
                    nxgraph.add_edge(chebi_id_1, chebi_id_2, rhea_id=rxn.rhea_id, dg_prime=1.0)
                    if rxn.rhea_id in rhea_edge_map:
                        rhea_edge_map[rxn.rhea_id].append((chebi_id_1, chebi_id_2))
                    else:
                        rhea_edge_map[rxn.rhea_id] = [(chebi_id_1, chebi_id_2)]

        return (nxgraph, rhea_edge_map)
