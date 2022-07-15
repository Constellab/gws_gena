# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from gws_core import (BadRequestException, BoolParam, ConfigParams, View,
                      ViewSpecs, ViewType)


class NetworkView(View):

    _type: ViewType = ViewType.NETWORK
    _data: "Network"
    _specs: ViewSpecs = {
        "refresh_layout":
        BoolParam(
            default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            human_name="Refresh layout",
            short_description="Set True to refresh layout"),
        "skip_orphans":
        BoolParam(
            default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            human_name="Remove orphans",
            short_description="Set True to remove orphan metabolites"),
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

    def to_dict(self, params: ConfigParams) -> dict:
        return {
            **super().to_dict(params),
            "data": self._data.dumps(refresh_layout=params["refresh_layout"])
        }
