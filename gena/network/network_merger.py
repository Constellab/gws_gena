# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.process import Process
from .network import Network

class NetworkMerger(Process):
    """
    NetworkMerger class.
    
    This process merge two networks
    """
    
    input_specs = { 'network_1': (Network,), 'network_2': (Network,) }
    output_specs = { 'network': (Network,) }
    config_specs = {}
    
    async def task(self):
        net = self.input['network_1'].copy()
        rnx_set = self.input['network_2'].copy()
        for comp_id in rnx_set.compounds:
            cmp = rnx_set.compounds[comp_id]
            cmp.network = None
            
        for rxn_id in rnx_set.reactions:
            rxn = rnx_set.reactions[rxn_id]
            rxn.network = None
            try:
                net.add_reaction(rxn)
            except:
                pass
            
        self.output['network'] = net
        