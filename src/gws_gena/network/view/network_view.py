# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict
from gws_core import View, BadRequestException, ViewSpecs

class NetworkView(View):
    
    _type = "network-view"
    _specs: ViewSpecs = {}
    _data: Dict

    def check_and_clean_data(self, data: Dict):
        """
        Check the data and return.

        Must be overloaded to implement adhoc data checker
        """

        if not isinstance(data, dict):
            raise BadRequestException("Network data must be a dictionnary")

        if "metabolites" not in data:
            raise BadRequestException("Invalid network data. No metabolites found.")
        
        if "reactions" not in data:
            raise BadRequestException("Invalid network data. No reactions found.")
        
        if "compartments" not in data:
            raise BadRequestException("Invalid network data. No compartments found.")

        return data


    def to_dict(self, **kwargs) -> dict:

        return {
            "type": self._type,
            "data": self._data
        }