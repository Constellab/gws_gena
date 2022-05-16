# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from .deadend_finder_helper import DeadendFinder

class GapFinder:

    @staticmethod
    def find(net) -> dict:
        """
        Get gap information
        """

        pathways = {}
        compounds = {}
        reactions = {}

        data = DeadendFinder.find(net)
        orphan_ids = [idx for idx in data.index if data.at[idx, "is_orphan"]]
        deadend_ids = [idx for idx in data.index if data.at[idx, "is_dead_end"]]

        for k in net.compounds:
            compounds[k] = {
                "name": "",
                "is_substrate": 0,
                "is_product": 0,
                "is_dead_end": k in deadend_ids,
                "is_orphan": k in orphan_ids,
            }

        for k in net.reactions:
            rxn = net.reactions[k]
            for c_id in rxn.substrates:
                comp = rxn.substrates[c_id]["compound"]
                compounds[c_id]["name"] = comp.name
                compounds[c_id]["is_substrate"] += 1
            for c_id in rxn.products:
                comp = rxn.products[c_id]["compound"]
                compounds[c_id]["name"] = comp.name
                compounds[c_id]["is_product"] += 1

        gaps = {
            "pathways": pathways,
            "reactions": reactions,
            "compounds": compounds
        }

        return gaps
