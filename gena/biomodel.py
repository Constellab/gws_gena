# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import uuid
from typing import List
from copy import deepcopy

from gws.exception.bad_request_exception import BadRequestException
from gws.resource import Resource
from gws.process import Process

from .network import Network, Compound, Reaction
from .context import Context, Variable

# ####################################################################
#
# BioModel class
#
# ####################################################################

class BioModel(Resource):
    """
    Class that represents a biomodel.
    
    A biomodel is defined by a set of networks related to a set of contexts. It
    can therefore be used for simulation and prediction.
    """
    
    _networks = None
    _network_contexts = None
    _contexts = None    
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
                'name': '',
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
            raise BadRequestException("The network must an instance of Network")
        if not network.is_saved():
            network.save()
        if network.uri in self.networks:
            raise BadRequestException(f"Network uri '{network.uri }'' duplicated")
        self.networks[network.uri] = network
        if related_context:
            if not isinstance(related_context, Context):
                raise BadRequestException("The related context must be an instance of Context")
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
            raise BadRequestException("The context must be an instance of Context")
        if not ctx.is_saved():
            ctx.save()
        if ctx.uri in self.contexts:
            raise BadRequestException(f"Context id {ctx.uri} duplicate")
        self.contexts[ctx.uri] = ctx
        if related_network:
            if not isinstance(related_network, Network):
                raise BadRequestException("The related network must be an instance of Network")
            if not related_network.is_saved():
                related_network.save()
            if not related_network.uri in self.networks:
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
            self.network_contexts[related_network.uri] = ctx
    
    # -- B --
    
    def __build_from_dump(self, data):
        for val in data.get("contexts",[]):
            ctx = Context.get(Context.uri == val["uri"])
            self.add_context(ctx) 
        for val in data.get("networks",[]):
            net = Network.get(Network.uri == val["uri"])
            self.add_network(net)
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
    
    def dumps(self, stringify=False, prettify=False, shallow=True) -> dict:
        _net_json = []
        _ctx_json = []
        _net_ctx_json = []
        for _net in self.networks.values():
            if shallow:
                _net_json.append( {"uri": _net.uri} )
            else:
                _net_json.append( _net.to_json() ) 
        for _ctx in self.contexts.values():
            if shallow:
                _ctx_json.append( {"uri": _ctx.uri} )
            else:
                _ctx_json.append( _ctx.to_json() )
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
        bm = BioModel()
        bm.__build_from_dump(data)
        bm.data["biomodel"] = bm.dumps()
        return bm
    

    def flatten(self, as_biomodel=False) -> dict:
        _comps = {}
        _mets = []
        _rxns = []

        def __get_network_uname(net):
            return ( net.name if net.name else "Network_"+str(net.uri) )

        _mapping = {} 
        _rev_mapping = {} 
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
                _met = deepcopy(k)
                _met["id"] = Compound._flatten_id(_met["id"], uname)
                #_met["name"] =  _met["name"]
                _met["compartment"] =  Compound._flatten_id(_met["compartment"], uname, is_compartment=True)
                _mets.append( _met )
            for k in tmp_json["reactions"]:
                _rxn = deepcopy(k)
                _original_rxn_id = _rxn["id"]
                _rxn["id"] = Reaction._flatten_id(_rxn["id"], uname)
                #_rxn["name"] = _rxn["name"]
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
                _meas = deepcopy(ctx.data["measures"])
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
            },
            "mapping": _mapping,
            "reverse_mapping": _rev_mapping
        }
        if as_biomodel:
            net = Network.from_json(_json["network"])
            ctx = Context.from_json(_json["context"])
            bio = FlatBioModel()

            bio.add_network(net, related_context=ctx)
            return bio
        else:
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
        return None

    # -- N --
    
    @property
    def name(self) -> str:
        """ 
        Get the name of the network
        
        :return: The name
        :rtype: `str`
        """
        
        return self.data.get("name", "")
    
    @name.setter
    def name(self, name:str):
        """ 
        Set the name of the network.
        
        :param name: The name
        :type name: `str`
        """
        
        self.data["name"] = name
    
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
    
    def save(self, *args, **kwargs):
        self.data["biomodel"] = self.dumps()
        return super().save(*args, **kwargs)
    
    # -- T --
    
    def to_json(self, stringify=False, prettify=False, shallow=True, **kwargs):
        """
        Returns a JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :param shallow: If True, the content of the biomodel is returned.
        :type shallow: bool
        :param kwargs: Theses parameters are passed to the super class
        :type kwargs: keyword arguments
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(**kwargs)
        _json["data"]["biomodel"] = self.dumps(shallow=shallow) #override to account for new updates
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
    
class FlatBioModel(BioModel):
    @property
    def flat_network(self) -> Network:
        return list(self.networks.values())[0]

class BioModelBuilder(Process):
    input_specs = { 'network': (Network,), 'context': (Context, None,) }
    output_specs = { 'biomodel': (BioModel,) }
    config_specs = {
        "use_context": {"type": bool, "default": True, "Description": "Set True to use the context, False otherwise."},
    }
    
    def check_before_task(self) -> bool:
        if self.get_param("use_context"):
            if not self.input["context"]:
                return False
        return True

    async def task(self):
        net = self.input["network"]
        bio = BioModel()
        bio.add_network(net)
        if self.get_param("use_context"):
            ctx = self.input["context"]
            bio.add_context(ctx, related_network=net)
        self.output["biomodel"] = bio

class BioModelFlattener(Process):
    input_specs = { 'biomodel': (BioModel,), }
    output_specs = { 'flat_biomodel': (FlatBioModel,) }
    config_specs = {}
    
    async def task(self):
        bio = self.input["biomodel"]
        self.output["flat_biomodel"] = bio.flatten(as_biomodel=True)