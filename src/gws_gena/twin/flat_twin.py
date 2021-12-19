# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
from typing import Dict

from gws_core import (BadRequestException, ConfigParams, DictRField, JSONView,
                      resource_decorator, view)

from ..network.network import Network
from .twin import Twin
from .twin_context import TwinContext


@resource_decorator("FlatTwin")
class FlatTwin(Twin):
    _mapping: Dict[str, dict] = DictRField()
    _reverse_mapping: Dict[str, str] = DictRField()

    def copy(self) -> 'FlatTwin':
        twin = super().copy()
        twin._mapping = copy.deepcopy(self._mapping)
        twin._reverse_mapping = copy.deepcopy(self._reverse_mapping)
        return twin

    @property
    def mapping(self) -> Dict[str, dict]:
        return self._mapping

    @property
    def reverse_mapping(self) -> Dict[str, str]:
        return self._reverse_mapping

    def dumps(self, *args, **kwargs):
        _json = super().dumps(*args, **kwargs)
        _json["mapping"] = self._mapping
        _json["reverse_mapping"] = self._reverse_mapping
        return _json

    @classmethod
    def loads(cls, flat_data) -> 'FlatTwin':
        if len(flat_data["networks"]) > 1:
            raise BadRequestException("More than one network found. The data are not compatible with a FlatTwin.")
        if len(flat_data["contexts"]) > 1:
            raise BadRequestException("More than one context found. The data are not compatible with a FlatTwin.")

        twin = cls()
        net = Network.loads(flat_data["networks"][0])
        ctx = TwinContext.loads(flat_data["contexts"][0])
        twin.add_network(net, related_context=ctx)
        twin.name = flat_data["name"]
        twin.description = flat_data["description"]
        twin._mapping = flat_data["mapping"]
        twin._reverse_mapping = flat_data["reverse_mapping"]
        return twin

    def dumps_flat(self) -> dict:
        return self.dumps()

    def get_flat_network(self):
        return list(self._networks.values())[0]

    def get_flat_context(self):
        return list(self._contexts.values())[0]

    # -- V --

    @view(view_type=JSONView, human_name="JSONView")
    def view_flat_network_as_json(self, params: ConfigParams) -> JSONView:
        net = self.get_flat_network()
        return net.view_as_json(params)
