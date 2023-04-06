# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ..flat_twin import FlatTwin, Twin

# ####################################################################
#
# TwinHelper class
#
# ####################################################################


class TwinFalltenerHelper:
    """ TwinFalltenerHelper """
    @classmethod
    def flatten(cls, twin: Twin) -> FlatTwin:
        """ Flatten the digital twin """
        data = twin.dumps_flat()
        return FlatTwin.loads(data)

    @classmethod
    def dumps_flat(cls, twin: Twin) -> dict:
        """ Generates a flat dump of the digital twin """

        all_compart_data = []
        all_met_data = []
        all_rxn_data = []

        _rxn_mapping = {}
        _rev_rxn_mapping = {}

        for net in twin.networks.values():
            net_data = net.dumps()

            # flatten all compartments ids
            for current_compart_data in net_data["compartments"]:
                compart_id = current_compart_data["id"]
                compart = net.compartments[compart_id]
                flat_compart_id = net.flatten_compartment_id(compart)
                current_compart_data["id"] = flat_compart_id
                current_compart_data["network_name"] = net.name
                all_compart_data.append(current_compart_data)

            # flatten all compound ids
            for current_met_data in net_data["metabolites"]:
                original_met_id = current_met_data["id"]
                met = net.compounds[original_met_id]
                current_met_data["id"] = net.flatten_compound_id(met)

                compart_id = current_met_data["compartment"]
                compart = net.compartments[compart_id]
                flat_compart_id = net.flatten_compartment_id(compart)
                current_met_data["compartment"] = flat_compart_id

                all_met_data.append(current_met_data)

            # flatten all reaction ids
            for current_rxn_data in net_data["reactions"]:
                original_rxn_id = current_rxn_data["id"]
                rxn = net.reactions[original_rxn_id]
                current_rxn_data["id"] = net.flatten_reaction_id(rxn)

                _rxn_mapping[current_rxn_data["id"]] = {
                    "network_name": net.name,
                    "reaction_id": original_rxn_id
                }

                if not net.name in _rev_rxn_mapping:
                    _rev_rxn_mapping[net.name] = {}
                _rev_rxn_mapping[net.name][original_rxn_id] = current_rxn_data["id"]

                current_rxn_stoichs = {}
                for original_met_id, stoich in current_rxn_data["metabolites"].items():
                    met = net.compounds[original_met_id]
                    flat_met_id = net.flatten_compound_id(met)
                    current_rxn_stoichs[flat_met_id] = stoich

                current_rxn_data["metabolites"] = current_rxn_stoichs
                all_rxn_data.append(current_rxn_data)

        all_measure_data = []
        for ctx in twin.contexts.values():
            related_network = twin.get_related_network(ctx)
            if related_network:
                ctx_data = ctx.dumps()
                for _meas in ctx_data["measures"]:
                    for _var in _meas["variables"]:
                        rxn_id = _var["reference_id"]
                        rxn = related_network.reactions[rxn_id]
                        _var["reference_id"] = related_network.flatten_reaction_id(rxn)

                all_measure_data.extend(ctx_data["measures"])
    
        data = {
            "name": twin.name,
            # "description": twin.description,
            "networks": [{
                "metabolites": all_met_data,
                "reactions": all_rxn_data,
                "compartments": all_compart_data,
            }],
            "contexts": [{
                "measures": all_measure_data
            }],
            "reaction_mapping": _rxn_mapping,
            "reverse_reaction_mapping": _rev_rxn_mapping
        }

        return data
