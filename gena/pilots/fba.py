# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import math

from gws.logger import Error, Info
from gws.model import Protocol
from gws.settings import Settings
from gws.plug import Source, Sink

from gena.file import *
from gena.recon import DraftRecon
from gena.gapfill import GapFiller

class FbaProtocol(Protocol):
    
    def __init__(self, *args, user = None, **kwargs):
        
        settings = Settings.retrieve()
        data_dir = settings.get_dir("gena:testdata_dir")
        
        ec_source = Source()
        biomass_source = Source()
        medium_source = Source()
        recon = DraftRecon()
        gapfiller = GapFiller()
        sink = Sink()
        
        processes = {
            "ec_loader": ec_loader,
            "medium_loader": medium_loader,
            "biomass_loader": biomass_loader,
            "recon": recon,
            "gapfiller": gapfiller
        }
        
        connectors = [
            ec_source>>"resource" | recon<<"ec_data",
            biomass_source>>"data" | recon<<"biomass_data",
            medium_source>>"data" | recon<<"medium_data",
            recon>>"network" | gapfiller<<"network",
            gapfiller>>"network" | "resource"<<sink
        ]
        
        super().__init__(
            processes = processes,
            connectors = connectors,
            interfaces = {},
            outerfaces = {},
            user = user,
            **kwargs
        )
