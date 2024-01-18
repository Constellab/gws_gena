# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, TypedDict

from gws_core import (BadRequestException, ConfigParams, DictRField, JSONView,
                      Resource, ResourceService, ResourceSet, StrRField,
                      resource_decorator, view)

from ..context.context import Context
from ..context.variable import Variable
from ..network.network import Network
from .typing.twin_typing import TwinDict


@resource_decorator("Twin", human_name="Twin", short_description="Twin of cell metabolism")
class Twin(ResourceSet):
    """
    Class that represents a twin.

    A twin is defined by a set of networks related to a set of contexts. It
    can therefore be used for simulation and prediction.
    """
    DEFAUTL_NAME = "twin"
    # description: str = StrRField(default_value="", searchable=True)
    network_contexts: Dict[str, str] = DictRField()

    def __init__(self):
        super().__init__()
        if not self.name:
            self.name = self.DEFAUTL_NAME

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
        if not self.resource_exists(ctx.name):
            # raise BadRequestException(f'The context "{ctx.name}" duplicate')
            self.add_resource(ctx)

        if related_network:
            if not isinstance(related_network, Network):
                raise BadRequestException("The related network must be an instance of Network")
            if not self.resource_exists(related_network.name):
                raise BadRequestException("The related networks is not found")
            if related_network.name in self.network_contexts:
                raise BadRequestException(f'The network "{related_network.name}" is already related to a context')

            # ckeck that the context is consistent with the related network
            reaction_ids = related_network.get_reaction_ids()
            compound_ids = related_network.get_compound_ids()

            for measure in ctx.reaction_data.values():
                for variable in measure.variables:
                    if not variable.reference_id in reaction_ids:
                        raise BadRequestException(
                            f"The reaction '{variable.reference_id}' of the context measure '{measure.id}' is not found in the list of reactions")

            for measure in ctx.compound_data.values():
                for variable in measure.variables:
                    if not variable.reference_id in compound_ids:
                        raise BadRequestException(
                            f"The compound '{variable.reference_id}' of the context measure '{measure.id}' is not found in the list of compounds")

            self.network_contexts[related_network.name] = ctx.name

    # -- B --

    # -- C --

    @property
    def contexts(self):
        """ Get all contexts """
        contexts = {}
        for name in self.network_contexts.values():
            contexts[name] = self.get_resource(name)
        return contexts

    def copy(self):
        """ Copy the twin """
        twin = type(self)()
        twin.name = self.name
        # twin.description = self.description
        # keep same networks
        for net in self.networks.values():
            twin.add_network(net.copy())
        for ctx in self.contexts.values():
            twin.add_context(ctx.copy())
        twin.network_contexts = self.network_contexts.copy()
        return twin

    # -- D --

    def dumps(self, deep=False) -> dict:
        """ Dump the twin """
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
            "name": self.name,
            "networks": _net_json,
            "contexts": _ctx_json,
            "network_contexts": _net_ctx_json
        }
        return _json

    # -- F --

    def flatten(self) -> 'FlatTwin':
        """ Flatten the twin """
        from .helper.twin_flattener_helper import TwinFalltenerHelper
        return TwinFalltenerHelper.flatten(self)

    def dumps_flat(self) -> dict:
        """ Generate a flat dump of the twin """
        from .helper.twin_flattener_helper import TwinFalltenerHelper
        return TwinFalltenerHelper.dumps_flat(self)

    # -- F --

    # -- G --

    def get_related_network(self, ctx):
        """ Get the network related to a context """
        for net_name, ctx_name in self.network_contexts.items():
            if ctx_name == ctx.name:
                return self.get_resource(net_name)

        return None

    def get_related_context(self, net):
        """ Get the context related to a network """
        for net_name, ctx_name in self.network_contexts.items():
            if net_name == net.name:
                return self.get_resource(ctx_name)

        return None

    def get_summary(self):
        json_ = {
            "name": self.name,
            "networks": [],
            "contexts": []
        }

        for net in self.networks.values():
            json_["networks"].append(net.get_summary())

        for ctx in self.contexts.values():
            json_["contexts"].append({
                "Name": ctx.name,
                "Number of reaction data": len(ctx.reaction_data),
                "Number of compound data": len(ctx.compound_data)
            })
        return json_

    # -- L --

    @classmethod
    def loads(cls, data: TwinDict):
        """ Loads JSON data and creates a Twin """
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

        # twin.description = data.get("description", "")
        return twin

    # -- M --

    # -- N --

    @property
    def networks(self):
        """ Returns the networks """
        networks = {}
        for name in self.network_contexts:
            networks[name] = self.get_resource(name)
        return networks

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
        data = self.get_summary()
        j_view = JSONView()
        j_view.set_data(data)
        return j_view
