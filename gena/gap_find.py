# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import copy
from pandas import DataFrame

from gws.process import Process
from gws.resource import Resource
from gws.settings import Settings
from gws.logger import Error, Info
from gws.view import DictView
from .network import Network

class GapFinderResult(Resource):
    """
    GapFinderResult class
    """

    def __init__(self, *args, gaps=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            if gaps:
                self.data['gaps'] = gaps 
            else:
                self.data['gaps'] = {}

    def render__gaps__as_json(self):
        return self.data["gaps"]

    def render__compounds__as_table(self, filter_gaps_only=False, stringify=False, **kwargs) -> (str, DataFrame,):
        table: DataFrame = DictView.to_table(
            self.data["gaps"]["compounds"], 
            columns=["is_substrate", "is_product", "is_gap"]
        )

        if filter_gaps_only:
            table = table[ :, table["is_gap"] == True ]

        if stringify:
            return table.to_csv()
        else:
            return table

    def render__reactions__as_table(self, filter_gaps_only=False, stringify=False, **kwargs) -> (str, DataFrame,):
        table: DataFrame = DictView.to_table(
            self.data["gaps"]["reactions"], 
            columns=["name", "has_gap"]
        )

        if filter_gaps_only:
            table = table[ :, table["has_gap"] == True ]

        if stringify:
            return table.to_csv()
        else:
            return table

    def render__pathways__as_table(self, filter_gaps_only=False, stringify=False, **kwargs) -> (str, DataFrame,):
        table: DataFrame = DictView.to_table(
            self.data["gaps"]["pathways"], 
            columns=["name", "nb_reactions", "nb_gaps", "gap_ratio"]
        )

        if filter_gaps_only:
            table = table[ :, table["nb_gaps"] > 0 ]

        if stringify:
            return table.to_csv()
        else:
            return table

class GapFinder(Process):
    """
    GapFinder class.
    """
    
    input_specs = { 'network': (Network,) }
    output_specs = { 'result': (GapFinderResult,) }
    config_specs = { }
        
    async def task(self):        
        net = self.input["network"]
        gaps = self.extract_gaps(net)
        self.output["result"] = GapFinderResult(gaps = gaps)

    @staticmethod
    def extract_gaps(net)->dict:
        """
        Get gap information
        """

        pathways = {}
        compounds = {}
        reactions = {}
        for k in net.compounds:
            compounds[k] = {
                "name": "",
                "is_substrate": False,
                "is_product": False,
                "is_gap": False,
            }

        for k in net.reactions:
            rxn = net.reactions[k]
            for c_id in rxn._substrates:
                comp = rxn._substrates[c_id]["compound"]
                compounds[c_id]["name"] = comp.name
                compounds[comp.id]["is_substrate"] = True
            for c_id in rxn.products:
                comp = rxn.products[c_id]["compound"]
                compounds[c_id]["name"] = comp.name
                compounds[comp.id]["is_product"] = True

        # collect gaps
        for k in compounds: 
            compounds[k]["is_gap"] = False    
            if not compounds[k]["is_product"] or not compounds[k]["is_substrate"]:
                comp = net.compounds[k]
                if comp.is_steady:
                    compounds[k]["is_gap"] = True
        for k in net.reactions:
            rxn = net.reactions[k]
            reactions[k] = {
                "name": rxn.name,
                "has_gap": False
            }
            for c_id in rxn._substrates:
                if compounds[c_id]["is_gap"]:
                    reactions[k]["has_gap"] = True
                    break
            for c_id in rxn.products:
                if compounds[c_id]["is_gap"]:
                    reactions[k]["has_gap"] = True
                    break

            rxn_pathways = rxn.get_pathways() 
            if rxn_pathways:
                kegg_pathway = rxn_pathways.get("kegg")
                if kegg_pathway:
                    p_id = kegg_pathway["id"]
                    if p_id in pathways:
                        pathways[p_id]["nb_reactions"] += 1
                        if reactions[k]["has_gap"]:
                            pathways[p_id]["nb_gaps"] += 1
                    else:
                        _name = kegg_pathway["name"]
                        pathways[p_id] = {
                            "name": _name,
                            "nb_reactions": 1,
                            "nb_gaps": (1 if reactions[k]["has_gap"] else 0),
                            "gap_ratio": 0
                        }

        for k in pathways:
            pathways[k]["gap_ratio"] = pathways[k]["nb_gaps"] / pathways[k]["nb_reactions"]

        gaps = {
            "pathways": pathways,
            "reactions": reactions,
            "compounds": compounds
        }

        return gaps