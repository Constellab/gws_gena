# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import uuid
from typing import List

from gws.logger import Error
from gws.model import Model, Resource

from .network import Network, Compound, Reaction
from .context import Context


# ####################################################################
#
# Biomodel class
#
# ####################################################################

class Biomodel(Resource):
    """
    Class that represents a biomodel.
    
    A biomodel is defined by a set of networks related to a set of contexts. It
    can therefore be used for simulation and prediction.
    """
    
    _networks = None
    _network_contexts = None
    _contexts = None
    
    _fts_fields = {'title': 2.0, 'description': 1.0}
    _table_name = "gena_biomodel"

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )

        self._networks = {}
        self._contexts = {}
        self._network_contexts = {}
        
        if self.data:
            self.__build_from_dump(self.data["biomodel"])
        else:
            self.data = {
                'title': '',
                'description': '',
                'networks': None,
                'contexts': None,
                'network_contexts': None,
            }
    
    # -- A --
    
    def add_network(self, network: 'Network', related_context: 'Context' = None):
        """
        Add a network to the biomodel

        :param network: The network to add
        :type network: `gena.network.Network`
        :param related_context: A context related to the network
        :type related_context: `gena.context.Context`
        """
        
        if not isinstance(network, Network):
            raise Error("Network", "add_network", "The network must an instance of Network")
        
        if not network.is_saved():
            network.save()
            
        if network.uri in self.networks:
            raise Error("Network", "add_network", f"Network id {name} duplicate")
            
        self.networks[network.uri] = network
        
        if related_context:
            if not isinstance(related_context, Context):
                raise Error("Network", "add_network", "The related context must be an instance of Context")
            
            self.add_context(related_context, network)
        
    def add_context(self, ctx: 'Context', related_network: 'Network' = None):  
        """
        Add a context to the biomodel

        :param context: The context to add
        :type context: `gena.context.Context`
        :param related_network: A network related to the context
        :type related_network: `gena.network.Network`
        """
        
        if not isinstance(ctx, Context):
            raise Error("Network", "add_context", "The context must be an instance of Context")
        
        if not ctx.is_saved():
            ctx.save()
            
        if ctx.uri in self.contexts:
            raise Error("Network", "add_context", f"Context id {ctx.uri} duplicate")
        
        self.contexts[ctx.uri] = ctx
        
        if related_network:
            if not isinstance(related_network, Network):
                raise Error("Network", "add_context", "The related network must be an instance of Network")
            
            if not related_network.is_saved():
                related_network.save()
            
            if not related_network.uri in self.networks:
                raise Error("Network", "add_context", f"The related networks is not found")
            
        
            self.network_contexts[related_network.uri] = ctx
    
    # -- B --
    
    def __build_from_dump(self, data):
        
        for val in data.get("contexts",[]):
            ctx = Context.get(Context.uri == val["uri"])
            self.add_context(ctx)
            
        for val in data.get("networks",[]):
            net = Network.get(Network.uri == val["uri"])
            self.add_network(ctx)
        
        net_ctx = data.get("network_contexts",[])
        for net_ctx in data.get("network_contexts",[]):
            net_uri = net_ctx["network_uri"]
            ctx_uri = net_ctx["context_uri"]
            self.network_contexts[net_uri] = self.contexts[ctx_uri]
            
    # -- C --
    
    @property
    def contexts(self):
        return self._contexts
    
    # -- D --
    
    @property
    def description(self) -> str:
        """ 
        Set the description of the compartment.
        
        :param description: The description
        :type description: `str`
        """
        
        return self.data.get("description")
    
    @description.setter
    def description(self, desc:str ):
        """ 
        Set the description of the compartment
        
        :return: The description
        :rtype: `str`
        """
        
        self.data["description"] = ""
    
    def dumps(self, stringify=False, prettify=False, expand=False) -> dict:
        _net_json = []
        _ctx_json = []
        _net_ctx_json = []
        
        for _net in self.networks.values():
            if expand:
                _net_json.append( _net.to_json() )
            else:
                _net_json.append( {"uri": _net.uri} )
            
        for _ctx in self.contexts.values():
            if expand:
                _ctx_json.append( _ctx.to_json() )
            else:
                _ctx_json.append( {"uri": _ctx.uri} )
        
        for _net_uri in self.network_contexts:
            _ctx = self.network_contexts[_net_uri]
            _net_ctx_json.append({
                "network_uri": _net_uri, 
                "context_uri": _ctx.uri
            })
        
        _json = {
            "networks": _net_json,
            "contexts": _ctx_json,
            "network_contexts": _net_ctx_json
        }
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
        
    # -- F --
    
    @classmethod
    def from_json(cls, data: dict):
        bm = Biomodel()
        bm.__build_from_dump(data)
        bm.data["biomodel"] = bm.dumps()
        return bm
    

    def flatten(self, remove_factors=False) -> dict:
        _comps = {}
        _mets = []
        _rxns = []

        def __get_network_uname(net):
            return (net.title if net.title else "network") + str(net.id)
            
        for net in self.networks.values():
            tmp_json = net.data["network"]
            if not net.is_saved():
                net.save()
            
            uname = __get_network_uname(net)
            
            for k in tmp_json["compartments"]:
                c_name = Compound._flatten_id(k, uname, is_compartment=True)
                c_desc = tmp_json["compartments"][k]
                _comps[c_name] = c_desc

            for k in tmp_json["metabolites"]:
                _met = k.copy()
                _met["id"] = Compound._flatten_id(_met["id"], uname)
                _met["name"] =  _met["name"]
                _met["compartment"] =  Compound._flatten_id(_met["compartment"], uname, is_compartment=True)
                _mets.append( _met )

            for k in tmp_json["reactions"]:
                _rxn = k.copy()
                _rxn["id"] = Reaction._flatten_id(_rxn["id"], uname)
                _rxn["name"] = _rxn["name"]
                
                _rxn_mets = {}
                for _met_name in _rxn["metabolites"]:
                    _flat_met_name = Compound._flatten_id(_met_name, uname)
                    _rxn_mets[_flat_met_name] = _rxn["metabolites"][_met_name]

                _rxn["metabolites"] = _rxn_mets                
                _rxns.append( _rxn )
        
        _meas = []
        for ctx in self.contexts.values():
            related_network = self._get_related_network(ctx)
            if related_network:
                uname = __get_network_uname(related_network)
                _meas = ctx.data["measures"].copy()
                for k in range(0, len(_meas)):
                    for var in _meas[k]["variables"]:
                         var["reference_id"] = Reaction._flatten_id(var["reference_id"], uname)
        
        _json = {
            "is_flat": True,
            "network": {
                "metabolites": _mets,
                "reactions": _rxns,
                "compartments": _comps,
            },
            "context": {
                "measures": _meas
            }
        }

        return _json
    
    # -- G --
    
    def _get_related_network(self, ctx):
        for net_uri in self.network_contexts:
            net_ctx = self.network_contexts[net_uri]
            if ctx == net_ctx:
                return self.networks[net_uri]
        
        return None
    
    def _get_related_context(self, net):
        for net_uri in self.network_contexts:
            if net.uri == net_uri:
                ctx = self.network_contexts[net_uri]
                return ctx
        
        return Nones

        
    # -- N --
    
    @property
    def name(self):
        """ 
        Get the name of the compartment
        
        Alias of :meth:`get_title` 
        :return: The name
        :rtype: `str`
        """
        
        return self.get_title()
    
    @name.setter
    def name(self, name:str):
        """ 
        Set the name of the compartment.
        
        Alias of :meth:`set_title` 
        :param name: The name
        :type name: `str`
        """
        
        return self.set_title(name)
    
    @property
    def networks(self):
        return self._networks
    
    @property
    def network_contexts(self):
        return self._network_contexts
    
    @property
    def number_of_compounds(self):
        c = 0
        for k in self.networks:
            net = self.networks[k]
            c += len(net.compounds)
        
        return c
    
    @property
    def number_of_reactions(self):
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
    
    def save(self, *args, **kwargs):
        self.data["biomodel"] = self.dumps()
        return super().save(*args, **kwargs)
    
    # -- T --
    
    def to_json(self, stringify=False, prettify=False, expand=False, **kwargs):
        """
        Returns a JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :param expand: If True, the  content of the biomodel is expanded. False otherwise.
        :type expand: bool
        :param kwargs: Theses parameters are passed to the super class
        :type kwargs: keyword arguments
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(**kwargs)
        _json["data"]["biomodel"] = self.dumps(expand=expand) #override to account for new updates
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json  
        
    # -- U --
    
    @staticmethod
    def _unflat(text):
        return text.split(":")