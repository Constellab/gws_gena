# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy

from gws_biota import Compound as BiotaCompound
from gws_biota import Reaction as BiotaReaction

from ..unicell.unicell import Unicell


class BiggMapper:

    @classmethod
    def _convert_bigg_annotation_list_to_dict(cls, annotation):
        if isinstance(annotation, list):
            annotation_dict = {}
            for annotation_val in annotation:
                k = annotation_val[0]
                v = annotation_val[1]
                if k not in annotation_dict:
                    annotation_dict[k] = []
                if "http" in v:
                    v = v.split("/")[-1]
                annotation_dict[k].append(v)
        return annotation_dict

    @classmethod
    def create_mapping_dict(cls, data):
        unicell = Unicell.create_network()
        unicell_comps = {comp.chebi_id: comp for comp in unicell.compounds.values()}
        unicell_rxns = {rxn.rhea_id: rxn for rxn in unicell.reactions.values()}

        # load biota compounds
        query = BiotaCompound.select().where(BiotaCompound.chebi_id.in_(list(unicell_comps.keys())))
        biota_comps = {}
        for c in query:
            biota_comps[c.chebi_id] = c

        # load biota reactions
        query = BiotaReaction.select().where(BiotaReaction.rhea_id.in_(list(unicell_rxns.keys())))
        biota_rxns = {}
        for r in query:
            biota_rxns[r.rhea_id] = r

        comp_table = {}
        rxn_table = {}

        # prepare compounds
        ckey = "compounds" if "compounds" in data else "metabolites"
        for comp_data in data[ckey]:
            # it is maybe a bigg data format
            annotation = comp_data.get("annotation")
            if annotation is not None:
                if isinstance(annotation, list):
                    annotation = cls._convert_bigg_annotation_list_to_dict(annotation)

                chebi_ids = annotation.get("chebi", []) or annotation.get("CHEBI", [])
                if isinstance(chebi_ids, str):
                    chebi_ids = [chebi_ids]

                chebi_ids = [val if val.startswith("CHEBI") else "CHEBI:"+val for val in chebi_ids]

                for chebi_id in chebi_ids:
                    if chebi_id in unicell_comps:
                        comp = unicell_comps[chebi_id]
                        comp_table[comp_data["id"]] = biota_comps[chebi_id]
                        break

        # prepare reactions
        for rxn_data in data["reactions"]:
            annotation = rxn_data.get("annotation")
            if annotation is not None:
                if isinstance(annotation, list):
                    annotation = cls._convert_bigg_annotation_list_to_dict(annotation)

                rhea_ids = annotation.get("rhea", [])
                if isinstance(rhea_ids, str):
                    rhea_ids = [rhea_ids]

                rhea_ids = [val if val.startswith("RHEA") else "RHEA:"+val for val in rhea_ids]

                for rhea_id in rhea_ids:
                    if rhea_id in unicell_rxns:
                        rxn = unicell_rxns[rhea_id]
                        rxn_table[rxn_data["id"]] = biota_rxns[rhea_id]
                        break

        return {"compounds": comp_table, "reactions": rxn_table}
