# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.model import Process
from gena.network import Reaction
from gws.logger import Error

from .data import ECData
from .network import Network, ReactionDuplicate

class DraftRecon(Process):
    input_specs = { 'ec_data': (ECData,) }
    output_specs = { 'network': (Network,) }
    config_specs = {
        'tax_id': {"type": 'str', "default": '', "description": "The taxonomy id"},
        'tax_search_method': {"type": 'str', "default": 'bottom_up', "description": "If 'bottom_up', the algorithm will to traverse the taxonomy tree to search in the higher taxonomy levels until a reaction is found. If 'none', the algorithm will only search at the given taxonomy level given by `tax_id`"}
    }
    
    async def task(self):
        ec_data = self.input['ec_data']
        ec_list = ec_data.get_ec_numbers(rtype="list")
        
        net = Network()
        tax_id = self.get_param('tax_id')
        
        for ec in ec_list:
            ec = str(ec).strip()
            is_incomplete_ec = ("-" in ec)
            
            if is_incomplete_ec:
                net.data["partial_ec_numbers"].append(ec)
            else:
                try:
                    rxns = Reaction.from_biota(ec_number=ec, network=net, tax_id=tax_id)
                    if not rxns:
                        net.data["not_found_ec_numbers"].append(ec)
                except ReactionDuplicate:
                    pass
                except Exception as err:
                    #raise Error(err)
                    net.data["errored_ec_numbers"].append(ec)
        
        self.output["network"] = net
        
class GapFiller(Process):
    pass