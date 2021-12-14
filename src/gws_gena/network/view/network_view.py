# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from gws_core import BadRequestException, View, ViewSpecs
from pandas import DataFrame


class NetworkView(View):

    _type = "network-view"
    _data: "Network"
    _specs: ViewSpecs = {
        **View._specs
    }

    def __init__(self, data):
        super().__init__()
        self._check_and_set_data(data)

    def _check_and_set_data(self, data: Dict):
        """
        Check the data and return.

        Must be overloaded to implement adhoc data checker
        """
        from ..network import Network
        if not isinstance(data, Network):
            raise BadRequestException("NetworkView data must be an instance of Network")

        self._data = data

    def to_dict(self, *args, **kwargs) -> dict:
        return {
            **super().to_dict(*args, **kwargs),
            "data": self._data.dumps()
        }
