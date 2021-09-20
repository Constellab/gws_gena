# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import TypedDict
from copy import deepcopy

from gws_core import BadRequestException
from gws_core import JSONDict, resource_decorator, SerializedResourceData, ResourceService

from ..network.network import Network, Compound, Reaction
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

@resource_decorator("Twin", serializable_fields=["uref", "name", "description"])
class Twin(JSONDict):
    """
    Class that represents a twin.
    
    A twin is defined by a set of networks related to a set of contexts. It
    can therefore be used for simulation and prediction.
    """
    
    DEFAULT_NAME = "twin"
    uref: str = ""
    name: str = ""
    description: str = ""

    _networks = None
    _network_contexts = None
    _contexts = None    
    _table_name = "gena_twin"

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self._networks = {}
        self._contexts = {}
        self._network_contexts = {}

        if "twin" in self.binary_store:
            twin_dict = self.binary_store["twin"]
            self._build_from_dump(twin_dict)
        else:
            self.binary_store["twin"] = TwinDict(
                name = self.DEFAULT_NAME,
                networks = [],
                contexts = [],
                network_contexts = []
            )

        # net_dict = self._get_twin_dict_from_store()
        # if net_dict:
        #     self._build_from_dump(net_dict)
 
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
        if network.uref in self.networks:
            raise BadRequestException(f"Network uri '{network.uref }'' duplicated")
        self.networks[network.uref] = network
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
        if ctx.uref in self.contexts:
            raise BadRequestException(f"TwinContext id {ctx.uref} duplicate")
        self.contexts[ctx.uref] = ctx
        if related_network:
            if not isinstance(related_network, Network):
                raise BadRequestException("The related network must be an instance of Network")
            if not related_network.uref in self.networks:
                raise BadRequestException("The related networks is not found")
            # ckeck that the context is consistent with the related network 
            reaction_ids = related_network.get_reaction_ids()
            for k in ctx.measures:
                measure = ctx.measures[k]
                for v in measure.variables:
                    if v.reference_type == Variable.REACTION_REFERENCE_TYPE:
                        if not v.reference_id in reaction_ids:
                            raise BadRequestException(f"The reaction '{v.reference_id}' of the context measure '{measure.id}' is not found in the list of reactions")
                    else:
                        raise BadRequestException(f"Invalid reference type '{v.reference_type}' for the context measure '{measure.id}'")
            self.network_contexts[related_network.uref] = ctx
    
    # -- B --
    
    def _build_from_dump_and_set_store(self, data):
        self._build_from_dump(data)
        self._set_twin_dict_in_store(data)

    def _build_from_dump(self, data):
        nets = {}
        for val in data.get("networks",[]):
            net = Network.from_json(val)
            nets[net.uref] = net
            self.add_network(net)

        for val in data.get("contexts",[]):
            ctx = TwinContext.from_json(val)
            current_ctx_uref = ctx.uref
            for net_ctx in data.get("network_contexts",[]):
                ctx_uref = net_ctx["context_uref"]
                if ctx_uref == current_ctx_uref:
                    net_uref = net_ctx["network_uref"]
                    self.add_context(ctx, related_network=nets[net_uref])
                    break

        self.name = data.get("name","")
        self.description = data.get("description","")

    # -- C --
    
    @property
    def contexts(self):
        return self._contexts
    
    # -- D --

    def dumps(self, deep=False) -> dict:
        _net_json = []
        _ctx_json = []
        _net_ctx_json = []
        for _net in self.networks.values():
            if not deep:
                _net_json.append({"uref": _net.uref})
            else:
                _net_json.append({
                    "uref": _net.uref,
                    "network": _net.dumps()
                }) 
        for _ctx in self.contexts.values():
            if not deep:
                _ctx_json.append({"uref": _ctx.uref})
            else:
                _ctx_json.append({
                    "uref": _ctx.uref,
                    "context": _ctx.dumps()
                })
        for _net_uref in self.network_contexts:
            _ctx = self.network_contexts[_net_uref]
            _net_ctx_json.append({
                "network_uref": _net_uref, 
                "context_uref": _ctx.uref
            })
        _json = {
            "networks": _net_json,
            "contexts": _ctx_json,
            "network_contexts": _net_ctx_json
        }
        return _json
        
    # -- F --
    
    @classmethod
    def from_json(cls, data: dict):
        if data.get("twin"):
            twin_dict = data["twin"]
        else:
            twin_dict = data

        bio = Twin()
        bio._build_from_dump_and_set_store(twin_dict)
        return bio

    def flatten(self) -> dict:
        _comps = {}
        _mets = []
        _rxns = []

        def __get_network_uname(net):
            return ( net.name if net.name else "Network_"+str(net.uref) )

        _mapping = {} 
        _rev_mapping = {} 
        for net in self.networks.values():
            tmp_json = net.binary_store["network"]
            uname = __get_network_uname(net)
            for k in tmp_json["compartments"]:
                c_name = Compound._flatten_id(k, uname, is_compartment=True)
                c_desc = tmp_json["compartments"][k]
                _comps[c_name] = c_desc
            for k in tmp_json["metabolites"]:
                _met = deepcopy(k)
                _met["id"] = Compound._flatten_id(_met["id"], uname)
                _met["compartment"] =  Compound._flatten_id(_met["compartment"], uname, is_compartment=True)
                _mets.append( _met )
            for k in tmp_json["reactions"]:
                _rxn = deepcopy(k)
                _original_rxn_id = _rxn["id"]
                _rxn["id"] = Reaction._flatten_id(_rxn["id"], uname)
                _rxn["lower_bound"] = _rxn["lower_bound"]
                _rxn["upper_bound"] = _rxn["upper_bound"]
                _mapping[ _rxn["id"] ] = {
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
                _rxns.append( _rxn )
        
        _meas = []
        for ctx in self.contexts.values():
            related_network = self._get_related_network(ctx)
            if related_network:
                uname = __get_network_uname(related_network)
                _meas = ctx.binary_store["context"]["measures"]
                for k in range(0, len(_meas)):
                    for var in _meas[k]["variables"]:
                         var["reference_id"] = Reaction._flatten_id(var["reference_id"], uname)

        _json = {
            "name": self.name,
            "description": self.description,
            "twin":{
                "is_flat": True,
                "networks": [{
                    "metabolites": _mets,
                    "reactions": _rxns,
                    "compartments": _comps,
                }],
                "contexts": [{
                    "measures": _meas
                }],
                "mapping": _mapping,
                "reverse_mapping": _rev_mapping,
            },
        }
        return _json
            
    
    # -- G --
    
    def _get_twin_dict_from_store(self) -> dict:
        return self.binary_store.get("twin",{})
        
    def _get_related_network(self, ctx):
        for net_uri in self.network_contexts:
            net_ctx = self.network_contexts[net_uri]
            if ctx == net_ctx:
                return self.networks[net_uri]
        return None
    
    def _get_related_context(self, net):
        for net_uri in self.network_contexts:
            if net.uref == net_uri:
                ctx = self.network_contexts[net_uri]
                return ctx
        return None

    # -- N --

    @property
    def networks(self)-> dict:
        return self._networks
    
    @property
    def network_contexts(self) -> dict:
        return self._network_contexts
    
    @property
    def number_of_compounds(self) -> int:
        c = 0
        for k in self.networks:
            net = self.networks[k]
            c += len(net.compounds)
        return c
    
    @property
    def number_of_reactions(self) -> int:
        c = 0
        for k in self.networks:
            net = self.networks[k]
            c += len(net.reactions)
        return c
    
    # -- R --
    
    def remove_all_contexts(self):
        self._contexts = {}
        self._network_contexts = {}
        
    # -- S --
    
    def refresh_binary_store(self):
        self._set_twin_dict_in_store(self.dumps(deep=True))

    def _set_twin_dict_in_store(self, data:dict) -> dict:
        self.binary_store["twin"] = data

    # -- T --
    
    def to_json(self, deep=False, **kwargs):
        """
        Returns a JSON string or dictionnary representation of the model.

        :param deep: If True, the content of the twin is returned.
        :type deep: bool
        :param kwargs: Theses parameters are passed to the super class
        :type kwargs: keyword arguments
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(**kwargs)
        _json["twin"] = self.dumps(deep=deep) #override to account for new updates
        return _json  
        
    # -- U --
    
    @staticmethod
    def _unflat(text):
        return text.split(":")
    
@resource_decorator("FlatTwin")
class FlatTwin(Twin):

    @classmethod
    def from_flat_dict(cls, data: dict ):
        twin = cls()
        net = Network.from_json(data["twin"]["networks"][0])
        ctx = TwinContext.from_json(data["twin"]["contexts"][0])
        twin.add_network(net, related_context=ctx)
        twin.name = data["name"]
        twin.description = data["description"]
        twin._set_twin_dict_in_store(data["twin"])
        return twin
        
    @property
    def flat_network(self) -> Network:
        return list(self.networks.values())[0]