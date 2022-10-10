# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

import networkx as nx
from gws_biota import Cofactor as BiotaCofactor
from gws_core import BadRequestException, Logger


class BaseGraph:
    """ Graph """
    _nxgraph = None
    _chebi_ids = None

    def __init__(self, network: 'Network' = None, use_chebi_ids_as_nodes: bool = False, skip_cofactors: bool = False):
        if network is None:
            self._graph = nx.Graph()
        else:
            nxgraph = self._create_nxgraph_from_network(
                network, use_chebi_ids_as_nodes=use_chebi_ids_as_nodes, skip_cofactors=skip_cofactors)
            self._nxgraph = nxgraph

    def find_neigbors(self, nodes: list, radius: int = 1, exclude_nodes: list = None):
        """ Finds the neighbors of a list of nodes """

        if not isinstance(nodes, list):
            raise BadRequestException("The nodes must be a list")
        neigbors = []
        for node in nodes:
            subgraph = nx.ego_graph(self._nxgraph, node, radius=radius)
            neigbors.extend(list(subgraph.nodes()))

        neigbors = list(set(neigbors))
        if exclude_nodes is not None:
            neigbors = [n for n in neigbors if n not in exclude_nodes]

        return neigbors

    def get_all_rhea_ids(self) -> List:
        """ Get all rhea ids """
        rhea_ids = set([edge[3] for edge in self._nxgraph.edges.data("rhea_id", default=None)])
        rhea_ids = [id_ for id_ in rhea_ids if id_ is not None]
        return rhea_ids

    def get_all_chebi_ids(self) -> List:
        """ Get all chebi ids """
        chebi_id_tuples = [edge[3] for edge in self._nxgraph.edges.data("chebi_ids", default=None)]
        chebi_ids = set()
        for list_ in chebi_id_tuples:
            chebi_ids.update(*list_)
        chebi_ids = [id_ for id_ in chebi_ids if id_ is not None]
        return chebi_ids

    def get_nx_graph(self):
        """ Get nx graph """
        return self._nxgraph

    # def edge_disjoint_paths(self, source, target, flow_func=None, cutoff=None, auxiliary=None, residual=None):
    #     pass

    @classmethod
    def _create_nxgraph_from_network(
            cls, network: 'Network', use_chebi_ids_as_nodes: bool = False, skip_cofactors: bool = False):
        """ Construct a `Graph` from a `Network` """

        added_rhea_ids = []
        is_warning_shown = False
        nxgraph = nx.Graph()

        cofactor_list: List[str] = BiotaCofactor.get_factors_as_list()
        for rxn in network.reactions.values():
            if rxn.rhea_id in added_rhea_ids:
                continue

            for comp1 in rxn.substrates.values():
                if use_chebi_ids_as_nodes:
                    comp_id_1 = comp1.compound.chebi_id or comp1.compound.id
                else:
                    comp_id_1 = comp1.compound.id

                if not comp_id_1:
                    if not is_warning_shown:
                        Logger.warning("Reactions without rhea_id or compounds without chebi_id are ignored")
                        is_warning_shown = True
                    continue

                if skip_cofactors and comp_id_1 in cofactor_list:
                    continue

                for comp2 in rxn.products.values():
                    if use_chebi_ids_as_nodes:
                        comp_id_2 = comp2.compound.chebi_id or comp2.compound.id
                    else:
                        comp_id_2 = comp2.compound.id

                    if not comp_id_2:
                        if not is_warning_shown:
                            Logger.warning("Reactions without rhea_id or compounds without chebi_id are ignored")
                            is_warning_shown = True
                        continue

                    if skip_cofactors and comp_id_2 in cofactor_list:
                        continue

                    chebi_ids = (comp1.compound.chebi_id, comp2.compound.chebi_id)
                    nxgraph.add_edge(comp_id_1, comp_id_2, rxn_id=rxn.id,
                                     rhea_id=rxn.rhea_id, chebi_ids=chebi_ids, dg_prime=1.0)

            if rxn.rhea_id:
                added_rhea_ids.append(rxn.rhea_id)

        return nxgraph


class Graph(BaseGraph):
    pass


class BipartiteGraph(BaseGraph):

    @classmethod
    def _create_nxgraph_from_network(
            cls, network: 'Network', use_chebi_ids_as_nodes: bool = False, skip_cofactors: bool = False):
        """ Construct a `Graph` from a `Network` """

        added_rhea_ids = []
        is_warning_shown = False
        nxgraph = nx.Graph()

        cofactor_list: List[str] = BiotaCofactor.get_factors_as_list()
        for rxn in network.reactions.values():
            if rxn.rhea_id in added_rhea_ids:
                continue

            for comp1 in rxn.substrates.values():
                if use_chebi_ids_as_nodes:
                    comp_id_1 = comp1.compound.chebi_id or comp1.compound.id
                else:
                    comp_id_1 = comp1.compound.id

                if not comp_id_1:
                    if not is_warning_shown:
                        Logger.warning("Reactions without rhea_id or compounds without chebi_id are ignored")
                        is_warning_shown = True
                    continue

                if skip_cofactors and comp_id_1 in cofactor_list:
                    continue

                nxgraph.add_edge(comp_id_1, rxn.id, rxn_id=rxn.id,
                                 rhea_id=rxn.rhea_id, chebi_ids=(comp_id_1,), dg_prime=1.0)

            for comp2 in rxn.products.values():
                if use_chebi_ids_as_nodes:
                    comp_id_2 = comp2.compound.chebi_id or comp2.compound.id
                else:
                    comp_id_2 = comp2.compound.id

                if not comp_id_2:
                    if not is_warning_shown:
                        Logger.warning("Reactions without rhea_id or compounds without chebi_id are ignored")
                        is_warning_shown = True
                    continue

                if skip_cofactors and comp_id_2 in cofactor_list:
                    continue

                nxgraph.add_edge(rxn.id, comp_id_2, rxn_id=rxn.id,
                                 rhea_id=rxn.rhea_id, chebi_ids=(comp_id_2,), dg_prime=1.0)

            if rxn.rhea_id:
                added_rhea_ids.append(rxn.rhea_id)

        return nxgraph
