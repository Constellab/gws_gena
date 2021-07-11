# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import abc
from pandas import DataFrame
from gws.logger import Error
from gws.resource import Resource

class AbstractFBAResult(Resource):
    
    @abc.abstractmethod
    def render__fluxes__as_table(self) -> DataFrame:
        return NotImplemented
    
    @abc.abstractmethod
    def render__sv__as_table(self) -> DataFrame:
        return NotImplemented
