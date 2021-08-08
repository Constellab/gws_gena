from .network.network import Network
from .network.network_merger import NetworkMerger

class __info__: 
    name = "Gena: Genome-based network analysis"
    desc = "This brick provides core features for genome-scale metabolic network reconstruction and analysis"
    doc = """ """
    tree = {
        ":Network":{
            ":Data": {
                "doc": "",
                "type" : Network,
            },
            ":Misc": {
                ":Merger": {
                    "doc": "",
                    "type" : NetworkMerger,
                },
            },
        }
    }