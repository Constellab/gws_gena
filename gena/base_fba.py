# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame
from gws.logger import Error
from gws.model import Resource

class AbstractFBAResult(Resource):
    
    def render__fluxes__as_table(self) -> DataFrame:
        raise Error("AbstractFBAResult", "render__fluxes__as_table", "Not implemented")
    
    def render__sv__as_table(self) -> DataFrame:
        raise Error("AbstractFBAResult", "render__sv__as_table", "Not implemented")
