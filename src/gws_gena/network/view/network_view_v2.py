
from typing import Dict

import networkx as nx
from gws_core import (BadRequestException, BoolParam, ConfigParams, StrParam,
                      View, ViewSpecs, ViewType)

from ..graph.graph import BipartiteGraph


class NetworkViewV2(View):

    _type: ViewType = ViewType.NETWORK
    _data: "Network"
    _specs: ViewSpecs = {}

    def __init__(self, data):
        super().__init__()
        self._check_and_set_data(data)

    def _check_and_set_data(self, data: Dict):
        """
        Check the data and return.

        Must be overloaded to implement adhoc data checker
        """
        from gws_gena.network.network_cobra import NetworkCobra
        if not isinstance(data, NetworkCobra):
            raise BadRequestException(
                "NetworkView data must be an instance of NetworkCobra")

        self._data = data

    def data_to_dict(self, params: ConfigParams) -> dict:
        return self._data.dumps(refresh_layout=True)