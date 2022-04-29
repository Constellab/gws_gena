# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
from typing import Dict, TypedDict

from gws_core import (BadRequestException, ConfigParams, DictRField, JSONView,
                      Resource, ResourceService, ResourceSet, StrRField,
                      resource_decorator, view)

from ..context.context import Context, Variable
from ..network.network import Compound, Network, Reaction

TwinDict = TypedDict("TwinDict", {
    "name": str,
    "networks": list,
    "contexts": list,
    "network_contexts": list
})

# ####################################################################
#
# Twin class
#
# ####################################################################


@resource_decorator("Twin", human_name="Twin", short_description="Twin of cell metabolism")
class Twin(ResourceSet):
    """
    Class that represents a twin.

    A twin is defined by a set of networks related to a set of contexts. It
    can therefore be used for simulation and prediction.
    """

    description: str = StrRField(default_value="", searchable=True)
    network_contexts: Dict[str, str] = DictRField()

    # -- A --

    def add_network(self, network: 'Network', related_context: 'Context' = None):
        """
        Add a network to the twin

        :param network: The network to add
        :type network: `gena.network.Network`
        :param related_context: A context related to the network
        :type related_context: `gena.context.Context`
        """

        if not isinstance(network, Network):
            raise BadRequestException("The network must an instance of Network")
        if self.resource_exists(network.name):
            raise BadRequestException(f"Network name '{network.name}'' duplicated")
        self.add_resource(network)
        if related_context:
            if not isinstance(related_context, Context):
                raise BadRequestException("The related context must be an instance of Context")
            self.add_context(related_context, network)

    def add_context(self, ctx: 'Context', related_network: 'Network' = None):
        """
        Add a context to the twin

        :param context: The context to add
        :type context: `gena.context.Context`
        :param related_network: A network related to the context
        :type related_network: `gena.network.Network`
        """

        if not isinstance(ctx, Context):
            raise BadRequestException("The context must be an instance of Context")
        if self.resource_exists(ctx.name):
            raise BadRequestException(f"Context name {ctx.name} duplicate")

        self.add_resource(ctx)

        if related_network:
            if not isinstance(related_network, Network):
                raise BadRequestException("The related network must be an instance of Network")
            if not self.resource_exists(related_network.name):
                raise BadRequestException("The related networks is not found")
            # ckeck that the context is consistent with the related network
            reaction_ids = related_network.get_reaction_ids()
            for k in ctx.measures:
                measure = ctx.measures[k]
                for v in measure.variables:
                    if v.reference_type == Variable.REACTION_REFERENCE_TYPE:
                        if not v.reference_id in reaction_ids:
                            raise BadRequestException(
                                f"The reaction '{v.reference_id}' of the context measure '{measure.id}' is not found in the list of reactions")
                    else:
                        raise BadRequestException(
                            f"Invalid reference type '{v.reference_type}' for the context measure '{measure.id}'")
            self.network_contexts[related_network.name] = ctx.name

    # -- B --

    # -- C --

    @property
    def contexts(self):
        contexts = {}
        for name in self.network_contexts.values():
            contexts[name] = self.get_resource(name)
        return contexts

    def copy(self):
        twin = type(self)()
        twin.name = self.name
        twin.description = self.description
        # keep same networks
        for net in self.networks.values():
            twin.add_network(net.copy())
        for ctx in self.contexts.values():
            twin.add_context(ctx.copy())
        twin.network_contexts = self.network_contexts.copy()
        return twin

    # -- D --

    def dumps(self, deep=False) -> dict:
        _net_json = []
        _ctx_json = []
        _net_ctx_json = []
        for _net in self.networks.values():
            if not deep:
                _net_json.append({"name": _net.name})
            else:
                _net_json.append({
                    "name": _net.name,
                    **_net.dumps()
                })
        for _ctx in self.contexts.values():
            if not deep:
                _ctx_json.append({"name": _ctx.name})
            else:
                _ctx_json.append({
                    "name": _ctx.name,
                    **_ctx.dumps()
                })
        for _net_name, _ctx_name in self.network_contexts.items():
            _net_ctx_json.append({
                "network_name": _net_name,
                "context_name": _ctx_name
            })
        _json = {
            "networks": _net_json,
            "contexts": _ctx_json,
            "network_contexts": _net_ctx_json
        }
        return _json

    # -- F --

    def flatten(self) -> 'FlatTwin':
        from .flat_twin import FlatTwin
        return FlatTwin.loads(self.dumps_flat())

    def dumps_flat(self) -> dict:
        _comps = {}
        _mets = []
        _rxns = []

        def __get_network_uname(net):
            return (net.name if net.name else "network")

        _mapping = {}
        _rev_mapping = {}
        
        for net in self.networks.values():
            net_data = net.dumps()
            uname = __get_network_uname(net)
            for k in net_data["compartments"]:
                c_name = Compound.flatten_id(k, uname, is_compartment=True)
                c_desc = net_data["compartments"][k]
                _comps[c_name] = c_desc

            for _met in net_data["metabolites"]:
                _met["id"] = Compound.flatten_id(_met["id"], uname)
                _met["compartment"] = Compound.flatten_id(_met["compartment"], uname, is_compartment=True)
                _mets.append(_met)

            for _rxn in net_data["reactions"]:
                _original_rxn_id = _rxn["id"]
                _rxn["id"] = Reaction.flatten_id(_rxn["id"], uname)
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
                    _flat_met_id = Compound.flatten_id(_met_id, uname)
                    stoich = _rxn["metabolites"][_met_id]
                    _rxn_mets[_flat_met_id] = stoich
                _rxn["metabolites"] = _rxn_mets
                _rxns.append(_rxn)

        _meas = []
        for ctx in self.contexts.values():
            related_network = self._get_related_network(ctx)
            if related_network:
                uname = __get_network_uname(related_network)
                ctx_data = ctx.dumps()
                _meas = copy.deepcopy(ctx_data["measures"])
                for k in range(0, len(_meas)):
                    for var in _meas[k]["variables"]:
                        var["reference_id"] = Reaction.flatten_id(var["reference_id"], uname)

        _json = {
            "name": self.name,
            "description": self.description,
            "networks": [{
                "metabolites": _mets,
                "reactions": _rxns,
                "compartments": _comps,
            }],
            "contexts": [{
                "measures": _meas
            }],
            "mapping": _mapping,
            "reverse_mapping": _rev_mapping
        }

        return _json

    # -- F --

    # -- G --

    def _get_related_network(self, ctx):
        for net_name, ctx_name in self.network_contexts.items():
            if ctx_name == ctx.name:
                return self.get_resource(net_name)

        return None

    def _get_related_context(self, net):
        for net_name, ctx_name in self.network_contexts.items():
            if net_name == net.name:
                return self.get_resource(ctx_name)

        return None

        # -- L --

    @classmethod
    def loads(cls, data: TwinDict):
        """ Loads JSON data nd creates a Twin """
        twin = cls()
        nets = {}
        for val in data.get("networks", []):
            net = Network.loads(val)
            nets[net.name] = net
            twin.add_network(net)

        for val in data.get("contexts", []):
            ctx = Context.loads(val)
            current_ctx_name = ctx.name
            for net_ctx in data.get("network_contexts", []):
                ctx_name = net_ctx["context_name"]
                if ctx_name == current_ctx_name:
                    net_name = net_ctx["network_name"]
                    twin.add_context(ctx, related_network=nets[net_name])
                    break

        twin.description = data.get("description", "")
        return twin

    # -- M --

    # -- N --

    @property
    def networks(self):
        """ Returns the networks """
        contexts = {}
        for name in self.network_contexts.keys():
            contexts[name] = self.get_resource(name)
        return contexts

    @property
    def number_of_compounds(self) -> int:
        """ Returns the number of compounds """
        count = 0
        for net in self.networks.values():
            count += len(net.compounds)
        return count

    @property
    def number_of_reactions(self) -> int:
        """ Returns the number of reactions """
        count = 0
        for net in self.networks.values():
            count += len(net.reactions)
        return count

    # -- R --

    def remove_all_contexts(self):
        """ Remove all the contexts """
        self.contexts = ResourceSet()
        self.network_contexts = {}

    # -- S --

    # -- T --

    # -- V --

    @view(view_type=JSONView, human_name="Summary")
    def view_as_summary(self, _: ConfigParams) -> JSONView:
        """ view as summary """
        j_view = {
            "name": self.name,
            "networks": [],
            "contexts": []
        }

        for net in self.networks.values():
            biomass_rxn = net.get_biomass_reaction()
            j_view["networks"].append({
                "name": net.name,
                "number of reactions": len(net.reactions),
                "number of compounds": len(net.compounds),
                "biomass reaction id": biomass_rxn.id,
                "biomass reaction name": biomass_rxn.name,
                "biomass reaction flat_id": Reaction.flatten_id(biomass_rxn.id, net.name)
            })

        for ctx in self.contexts.values():
            j_view["contexts"].append({
                "name": ctx.name,
                "number of measurements": len(ctx.measures)
            })

        return j_view
