# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
from typing import Dict, TypedDict

from gws_core import (BadRequestException, ConfigParams, DictRField, JSONDict,
                      JSONView, ResourceService, StrRField, TextView,
                      resource_decorator, view)

from ..network.network import Compound, Network, Reaction
from .twin_context import TwinContext, Variable

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


@resource_decorator("Twin")
class Twin(JSONDict):
    """
    Class that represents a twin.

    A twin is defined by a set of networks related to a set of contexts. It
    can therefore be used for simulation and prediction.
    """

    DEFAULT_NAME = "twin"
    name: str = StrRField(default_value="", searchable=True)
    description: str = StrRField(default_value="", searchable=True)
    _networks: Dict[str, Network] = DictRField()
    _contexts: Dict[str, TwinContext] = DictRField()
    _network_contexts: Dict[str, str] = DictRField()

    _table_name = "gena_twin"

    # -- A --

    def add_network(self, network: 'Network', related_context: 'TwinContext' = None):
        """
        Add a network to the twin

        :param network: The network to add
        :type network: `gena.network.Network`
        :param related_context: A context related to the network
        :type related_context: `gena.twin_context.TwinContext`
        """

        if not isinstance(network, Network):
            raise BadRequestException("The network must an instance of Network")
        if network.uid in self._networks:
            raise BadRequestException(f"Network uid '{network.uid }'' duplicated")
        self._networks[network.uid] = network
        if related_context:
            if not isinstance(related_context, TwinContext):
                raise BadRequestException("The related context must be an instance of TwinContext")
            self.add_context(related_context, network)

    def add_context(self, ctx: 'TwinContext', related_network: 'Network' = None):
        """
        Add a context to the twin

        :param context: The context to add
        :type context: `gena.twin_context.TwinContext`
        :param related_network: A network related to the context
        :type related_network: `gena.network.Network`
        """

        if not isinstance(ctx, TwinContext):
            raise BadRequestException("The context must be an instance of TwinContext")
        if ctx.uid in self._contexts:
            raise BadRequestException(f"TwinContext id {ctx.uid} duplicate")
        self._contexts[ctx.uid] = ctx
        if related_network:
            if not isinstance(related_network, Network):
                raise BadRequestException("The related network must be an instance of Network")
            if not related_network.uid in self._networks:
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
            self._network_contexts[related_network.uid] = ctx

    # -- B --

    # -- C --

    @property
    def contexts(self):
        return self._contexts

    def copy(self):
        twin = type(self)()
        twin.name = self.name
        twin.description = self.description
        # keep same networks
        twin._networks = {k: self._networks[k].copy() for k in self._networks}
        twin._contexts = {k: self._contexts[k].copy() for k in self._contexts}
        twin._network_contexts = copy.deepcopy(self._network_contexts)
        return twin

    # -- D --

    def dumps(self, deep=False) -> dict:
        _net_json = []
        _ctx_json = []
        _net_ctx_json = []
        for _net in self._networks.values():
            if not deep:
                _net_json.append({"uid": _net.uid})
            else:
                _net_json.append({
                    "uid": _net.uid,
                    **_net.dumps()
                })
        for _ctx in self._contexts.values():
            if not deep:
                _ctx_json.append({"uid": _ctx.uid})
            else:
                _ctx_json.append({
                    "uid": _ctx.uid,
                    **_ctx.dumps()
                })
        for _net_uid in self._network_contexts:
            _ctx = self._network_contexts[_net_uid]
            _net_ctx_json.append({
                "network_uid": _net_uid,
                "context_uid": _ctx.uid
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
            return (net.name if net.name else "network_"+str(net.id))

        _mapping = {}
        _rev_mapping = {}
        for net in self._networks.values():
            net_data = net.dumps()
            uname = __get_network_uname(net)
            for k in net_data["compartments"]:
                c_name = Compound._flatten_id(k, uname, is_compartment=True)
                c_desc = net_data["compartments"][k]
                _comps[c_name] = c_desc

            for _met in net_data["metabolites"]:
                _met["id"] = Compound._flatten_id(_met["id"], uname)
                _met["compartment"] = Compound._flatten_id(_met["compartment"], uname, is_compartment=True)
                _mets.append(_met)

            for _rxn in net_data["reactions"]:
                _original_rxn_id = _rxn["id"]
                _rxn["id"] = Reaction._flatten_id(_rxn["id"], uname)
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
                    _flat_met_id = Compound._flatten_id(_met_id, uname)
                    stoich = _rxn["metabolites"][_met_id]
                    _rxn_mets[_flat_met_id] = stoich
                _rxn["metabolites"] = _rxn_mets
                _rxns.append(_rxn)

        _meas = []
        for ctx in self._contexts.values():
            related_network = self._get_related_network(ctx)
            if related_network:
                uname = __get_network_uname(related_network)
                ctx_data = ctx.dumps()
                _meas = copy.deepcopy(ctx_data["measures"])
                for k in range(0, len(_meas)):
                    for var in _meas[k]["variables"]:
                        var["reference_id"] = Reaction._flatten_id(var["reference_id"], uname)

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
        for net_uid in self._network_contexts:
            ctx = self._network_contexts[net_uid]
            if ctx.uid == ctx.uid:
                return self._networks[net_uid]
        return None

    def _get_related_context(self, net):
        for net_uid in self._network_contexts:
            if net.uid == net_uid:
                ctx = self._network_contexts[net_uid]
                return ctx
        return None

    # -- L --

    @classmethod
    def loads(cls, data: TwinDict):
        twin = cls()
        nets = {}
        for val in data.get("networks", []):
            net = Network.loads(val)
            nets[net.uid] = net
            twin.add_network(net)

        for val in data.get("contexts", []):
            ctx = TwinContext.loads(val)
            current_ctx_uid = ctx.uid
            for net_ctx in data.get("network_contexts", []):
                ctx_uid = net_ctx["context_uid"]
                if ctx_uid == current_ctx_uid:
                    net_uid = net_ctx["network_uid"]
                    twin.add_context(ctx, related_network=nets[net_uid])
                    break

        twin.name = data.get("name", "")
        twin.description = data.get("description", "")
        return twin

    # -- M --

    # -- N --

    @property
    def networks(self):
        return self._networks

    @property
    def network_contexts(self):
        return self._network_contexts

    @property
    def number_of_compounds(self) -> int:
        c = 0
        for k in self._networks:
            net = self._networks[k]
            c += len(net.compounds)
        return c

    @property
    def number_of_reactions(self) -> int:
        c = 0
        for k in self._networks:
            net = self._networks[k]
            c += len(net.reactions)
        return c

    # -- R --

    def remove_all_contexts(self):
        self._contexts = {}
        self._network_contexts = {}

    # -- S --

    # -- T --

    # -- V --

    @view(view_type=TextView, default_view=True, human_name="InfoText")
    def view_as_table(self, params: ConfigParams) -> TextView:
        text = []
        text.append("Networks")
        text.append("--------")
        for net_id, net in self.networks.items():
            text.append(f"Network: {net_id}")
            text.append(f"- name: {net.name}")
            text.append(f"- description: {net.description}")
            text.append(f"- number of reactions: {len(net.reactions)}")
            text.append(f"- number of compounds: {len(net.compounds)}")
            text.append("")

        text.append("")
        text.append("Contexts")
        text.append("--------")
        for ctx_id, ctx in self.contexts.items():
            text.append(f"Context: {ctx_id}")
            text.append(f"- name: {ctx.name}")
            text.append(f"- description: {ctx.description}")
            text.append(f"- number of variables: {len(ctx.measures)}")
            text.append("")

        return TextView("\n".join(text))
