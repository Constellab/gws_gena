# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
from typing import Dict

from gws_core import (BadRequestException, ConfigParams, DictRField, JSONView,
                      resource_decorator, view, TypingStyle)

from ..context.context import Context
from ..network.network import Network
from .twin import Twin


@resource_decorator("FlatTwin", human_name="Flat twin",
                    short_description="Flat digital twin of cell metabolism",
                    style=TypingStyle.material_icon(material_icon_name='home', background_color='#FFCE8B'))
class FlatTwin(Twin):
    """ FlatTwin

    A flat digital twin of cell metabolism
    """

    _mapping: Dict[str, dict] = DictRField()
    _reverse_mapping: Dict[str, str] = DictRField()

    def copy(self) -> 'FlatTwin':
        twin = super().copy()
        twin._reaction_mapping = copy.deepcopy(self._reaction_mapping)
        twin._reverse_reaction_mapping = copy.deepcopy(self._reverse_reaction_mapping)
        return twin

    @property
    def reaction_mapping(self) -> Dict[str, dict]:
        return self._reaction_mapping

    @property
    def reverse_reaction_mapping(self) -> Dict[str, str]:
        return self._reverse_reaction_mapping

    def dumps(self, *args, **kwargs):
        data = super().dumps(*args, **kwargs)
        data["reaction_mapping"] = self._reaction_mapping
        data["reverse_reaction_mapping"] = self._reverse_reaction_mapping
        return data

    @classmethod
    def loads(cls, data) -> 'FlatTwin':
        """ Loads form a JSON dump """
        if len(data["networks"]) > 1:
            raise BadRequestException("More than one network found. The data are not compatible with a FlatTwin.")
        if len(data["contexts"]) > 1:
            raise BadRequestException("More than one context found. The data are not compatible with a FlatTwin.")

        twin: Twin = cls()

        net = Network.loads(data["networks"][0])
        if len(data["contexts"]) == 0:
            raise BadRequestException("No context defined. Cannot flattened")

        if len(data["contexts"]):
            ctx = Context.loads(data["contexts"][0])
            twin.add_network(net, related_context=ctx)

        twin.name = data["name"]
        # twin.description = data["description"]
        twin._reaction_mapping = data["reaction_mapping"]
        twin._reverse_reaction_mapping = data["reverse_reaction_mapping"]
        return twin

    def dumps_flat(self) -> dict:
        return self.dumps()

    def get_flat_network(self):
        """ Get the flat network """
        return list(self.networks.values())[0]

    def get_flat_context(self):
        """ Get the  flat context """
        return list(self.contexts.values())[0]

    # -- V --

    @view(view_type=JSONView, human_name="JSONView")
    def view_flat_network_as_json(self, params: ConfigParams) -> JSONView:
        net = self.get_flat_network()
        return net.view_as_json(params)
