# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.process import Process
from ..network.network import Network
from .gap_finder_result import GapFinderResult

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
                "is_substrate": 0,
                "is_product": 0,
                "is_gap": False,
                "is_orphan": False,
            }
 
        for k in net.reactions:
            rxn = net.reactions[k]
            for c_id in rxn._substrates:
                comp = rxn._substrates[c_id]["compound"]
                compounds[c_id]["name"] = comp.name
                compounds[c_id]["is_substrate"] += 1
            for c_id in rxn.products:
                comp = rxn.products[c_id]["compound"]
                compounds[c_id]["name"] = comp.name
                compounds[c_id]["is_product"] += 1

        # collect gaps
        for k in compounds: 
            is_orphan = False
            if compounds[k]["is_product"] and compounds[k]["is_substrate"]:
                is_gap = False
            elif compounds[k]["is_product"] > 1:
                is_gap = False #is linked to more than 1 reactions
            elif compounds[k]["is_substrate"] > 1:
                is_gap = False #is linked to more than 1 reactions
            else:
                is_gap = True
                if not compounds[k]["is_product"] and not compounds[k]["is_substrate"]:
                    is_orphan = True

            if is_gap:
                comp = net.compounds[k]
                if comp.is_steady:
                    compounds[k]["is_gap"] = True

            if is_orphan:
                compounds[k]["is_orphan"] = True

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