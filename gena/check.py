# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math
from gws.exception.bad_request_exception import BadRequestException
from gws.process import Process
from gws.csv import CSVData

from gena.network import Network

class IdentifCheckerResult(CSVData):
    pass

class IdentifChecker(Process):
    """
    NetworkMerger class.
    
    This process merge two networks
    """
    
    input_specs = { 'network': (Network,) }
    output_specs = { 'result': (IdentifCheckerResult,) }
    config_specs = {}
    
    async def task(self):
        net: Network = self.input['network']
        stoich = net.create_steady_stoichiometric_matrix()
        self.output['network'] = net
        