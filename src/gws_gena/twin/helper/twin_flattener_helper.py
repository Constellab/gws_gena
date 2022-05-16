# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy

from ...network.compound import Compound
from ...network.reaction import Reaction
from ..flat_twin import FlatTwin, Twin

# ####################################################################
#
# TwinHelper class
#
# ####################################################################


class TwinFalltenerHelper:

    @classmethod
    def flatten(cls, twin: Twin) -> FlatTwin:
        """ Flatten the digital twin """
        return FlatTwin.loads(twin.dumps_flat())

    @classmethod
    def dumps_flat(cls, twin: Twin) -> dict:
        """ Generates a flat dump of the digital twin """

        _comps = {}
        _mets = []
        _rxns = []

        _mapping = {}
        _rev_mapping = {}

        for net in twin.networks.values():
            net_data = net.dumps()
            for k in net_data["compartments"]:
                c_name = Compound.flatten_compartment_id(k, net.name)
                c_desc = net_data["compartments"][k]
                _comps[c_name] = c_desc

            for _met in net_data["metabolites"]:
                _met["id"] = Compound.flatten_compound_id(_met["id"], net.name)
                _met["compartment"] = Compound.flatten_compartment_id(_met["compartment"], net.name)
                _mets.append(_met)

            for _rxn in net_data["reactions"]:
                _original_rxn_id = _rxn["id"]
                _rxn["id"] = Reaction.flatten_id(_rxn["id"], net.name)
                _rxn["lower_bound"] = _rxn["lower_bound"]
                _rxn["upper_bound"] = _rxn["upper_bound"]
                _mapping[_rxn["id"]] = {
                    "network_name": net.name,
                    "reaction_id": _original_rxn_id
                }
                if not net.name in _rev_mapping:
                    _rev_mapping[net.name] = {}
                _rev_mapping[net.name][_original_rxn_id] = _rxn["id"]
                _rxn_mets = {}
                for _met_id in _rxn["metabolites"]:
                    _flat_met_id = Compound.flatten_compound_id(_met_id, net.name)
                    stoich = _rxn["metabolites"][_met_id]
                    _rxn_mets[_flat_met_id] = stoich
                _rxn["metabolites"] = _rxn_mets
                _rxns.append(_rxn)

        _measures = []
        for ctx in twin.contexts.values():
            related_network = twin.get_related_network(ctx)
            if related_network:
                ctx_data = ctx.dumps()
                for _meas in ctx_data["measures"]:
                    for _var in _meas["variables"]:
                        _var["reference_id"] = Reaction.flatten_id(_var["reference_id"], related_network.name)
                _measures.extend(ctx_data["measures"])

        _json = {
            "name": twin.name,
            "description": twin.description,
            "networks": [{
                "metabolites": _mets,
                "reactions": _rxns,
                "compartments": _comps,
            }],
            "contexts": [{
                "measures": _measures
            }],
            "mapping": _mapping,
            "reverse_mapping": _rev_mapping
        }

        return _json
