# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import copy

from gws.process import Process
from gws.resource import Resource
from gws.settings import Settings
from gws.logger import Error, Info

from .network import Network

class Gaps(Resource):
    pass

class GapFinder(Process):
    """
    GapChecker class.
    """
    
    input_specs = { 'network': (Network,) }
    output_specs = { 'network': (Gaps,) }
    config_specs = { }
        
    async def task(self):        
        input_net = self.input["network"]
        _gap_info = input_net._get_gap_info()
                
        self.output["network"] = output_net
