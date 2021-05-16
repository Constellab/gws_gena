# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import math

from gws.logger import Error, Info
from gws.model import Protocol
from gws.settings import Settings

from gena.file import *
from gena.recon import DraftRecon
from gena.gapfill import GapFiller

class ReconPilot(Protocol):
    
    def __init__(self, *args, user = None, **kwargs):
        
        settings = Settings.retrieve()
        data_dir = settings.get_dir("gena:testdata_dir")
        
        ec_loader = ECLoader()
        file_path = os.path.join(data_dir, "recon_ec_data.csv")
        ec_loader.set_param("file_path", file_path)
        ec_loader.set_param("ec_column_name", "EC Number")
        
        file_path = os.path.join(data_dir, "recon_medium.csv")
        medium_loader = MediumLoader()
        medium_loader.set_param("file_path", file_path)
        medium_loader.set_param("chebi_column_name", "Chebi ID")
        
        biomass_loader = BiomassLoader()
        file_path = os.path.join(data_dir, "recon_biomass.csv")
        biomass_loader.set_param("file_path", file_path)
        biomass_loader.set_param("biomass_column_name", "Biomass")
        biomass_loader.set_param("chebi_column_name", "Chebi ID")
        
        recon = DraftRecon()
        #recon.set_param('tax_id', "263815")  #target pneumocyctis
        
        gapfiller = GapFiller()
        #gapfiller.set_param('tax_id', "4753")    #fungi 
        #gapfiller.set_param('tax_id', "2759")    #eukaryota
        
        processes = {
            "ec_loader": ec_loader,
            "medium_loader": medium_loader,
            "biomass_loader": biomass_loader,
            "recon": recon,
            "gapfiller": gapfiller
        }
        
        connectors = [
            ec_loader>>"data" | recon<<"ec_data",
            biomass_loader>>"data" | recon<<"biomass_data",
            medium_loader>>"data" | recon<<"medium_data",
            recon>>"network" | gapfiller<<"network"
        ]
        
        super().__init__(
            processes = processes,
            connectors = connectors,
            interfaces = {},
            outerfaces = {},
            user = user,
            **kwargs
        )
