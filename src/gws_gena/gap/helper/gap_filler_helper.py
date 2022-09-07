# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
from typing import List

import networkx as nx
import pandas as pd
from gws_biota.unicell.unicell_service import \
    UnicellService as BiotaUnicellService
from pandas import DataFrame, Series

from ...helper.base_helper import BaseHelper
from ...network.graph.graph import Graph
from ...network.network import Network
from ...network.reaction.reaction import Reaction
from ..helper.gap_finder_helper import GapFinderHelper


class GapFillerHelper(BaseHelper):
    """ GapFinderHelper """

    def fill_gaps(self, net: Network, tax_id: str = None, weight: str = None) -> DataFrame:
        """ Find all gaps """

        rhea_ids = self.find_gap_filling_rhea_ids(net, tax_id=tax_id, weight=weight)
        self.log_info_message(f"{len(rhea_ids)} reaction(s) added")
        for rhea_id in rhea_ids:
            rxns = Reaction.from_biota(rhea_id=rhea_id)
            if not net.reaction_exists(rxns[0]):
                net.add_reaction(rxns[0])
                net.update_reaction_recon_tag(rxns[0].id, {"is_from_gap_fill": True})

        return net

    def find_gap_filling_rhea_ids(self, net: Network, tax_id: str = None, weight: str = None, partial: bool = True):
        """ Fill gaps """

        helper = GapFinderHelper()
        dead_ends = helper.find_deadend_compound_ids(net)
        if len(dead_ends) == 0:
            self.log_info_message("No dead-end metabolites found")
            return []
        else:
            self.log_info_message(f"{len(dead_ends)} dead-end metabolite(s) found")

        unicell = BiotaUnicellService.create_unicell(tax_id=tax_id)
        nodes = []
        for comp_id in dead_ends:
            comp = net.compounds[comp_id]
            if comp.is_cofactor():
                continue
            if comp.chebi_id not in unicell.get_compound_id_list():
                self.log_warning_message(
                    f"Compound {comp.chebi_id} is not found in the unicell. It is skipped!")
                continue
            nodes.append(comp.chebi_id)
        unicell_subgraph = unicell.neigbors_subgraph(nodes, radius=1)

        # only select edge able to fill gaps
        chebi_id_list = []
        for comp in net.compounds.values():
            chebi_id_list.append(comp.chebi_id)

        added_edges = []
        for edge in unicell_subgraph.edges:
            if (edge[0] in chebi_id_list) and (edge[1] in chebi_id_list):
                added_edges.append(edge)

        # net_graph = Graph(net)
        # nxgraph = copy.deepcopy(net_graph.get_nx_graph())
        # nxgraph.add_nodes_from(unicell_subgraph)
        # added_edges = list(nx.k_edge_augmentation(
        #     nxgraph, k=1, avail=unicell_subgraph.edges, weight=weight, partial=partial))

        added_edge_data = [unicell_subgraph.get_edge_data(*edge) for edge in added_edges]
        rhea_ids = [data["rhea_id"] for data in added_edge_data]
        return list(set(rhea_ids))
