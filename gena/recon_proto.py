# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import math

from gws.logger import Error, Info
from gws.model import Protocol, Process
from gws.settings import Settings
from gws.plug import Source, Sink, FIFO2
from gws.io import Interface, Outerface
#from gws.file import *

from gena.data import ECImporter, MediumImporter, BiomassImporter
from gena.recon import DraftRecon
from gena.gap_fill import GapFiller

class ReconProto(Protocol):
    
    def __init__(self, *args, user = None, **kwargs):
        super().__init__(*args, user=user, **kwargs)
        if not self.is_built:
            # fifo2      
            ec_fifo = FIFO2()
            biomass_fifo = FIFO2()
            medium_fifo = FIFO2()
            # source
            ec_source = Source()
            biomass_source = Source()
            medium_source = Source()
            # importer
            ec_importer = ECImporter()
            ec_importer.set_param("ec_column_name", "EC Number")
            medium_importer = MediumImporter()
            medium_importer.set_param("chebi_column_name", "Chebi ID")
            biomass_importer = BiomassImporter()
            biomass_importer.set_param("biomass_column_name", "Biomass")
            biomass_importer.set_param("chebi_column_name", "Chebi ID")
            # other procs
            recon = DraftRecon()
            gapfiller = GapFiller()
            sink = Sink()
            
            processes = {
                # fifo2
                "ec_fifo": ec_fifo,
                "biomass_fifo": biomass_fifo,
                "medium_fifo": medium_fifo,
                # source
                "ec_source": ec_source,
                "medium_source": medium_source,
                "biomass_source": biomass_source,
                # importer
                "ec_importer": ec_importer,
                "medium_importer": medium_importer,
                "biomass_importer": biomass_importer,
                # other procs
                "draft_recon": recon,
                "gapfiller": gapfiller,
                "sink": sink
            }
            
            connectors = [
                ec_source>>"resource" | ec_fifo<<"resource_1",
                ec_importer>>"data" | ec_fifo<<"resource_2",
                (ec_fifo>>"resource").pipe(recon<<"ec_data", lazy=True),

                biomass_source>>"resource" | biomass_fifo<<"resource_1",
                biomass_importer>>"data" | biomass_fifo<<"resource_2",
                (biomass_fifo>>"resource").pipe(recon<<"biomass_data", lazy=True),

                medium_source>>"resource" | medium_fifo<<"resource_1",
                medium_importer>>"data" | medium_fifo<<"resource_2",
                (medium_fifo>>"resource").pipe(recon<<"medium_data", lazy=True),

                recon>>"network" | gapfiller<<"network",
                gapfiller>>"network" | sink<<"resource"
            ]
            
            interfaces = {
                # ec
                "ec_data": ec_fifo<<"resource_1",
                "ec_file": ec_importer<<"file",
                # biomass
                "biomass_data": biomass_fifo<<"resource_1",
                "biomass_file": biomass_importer<<"file",
                # medium
                "medium_data": medium_fifo<<"resource_1",
                "medium_file": medium_importer<<"file"
            }

            outerfaces = {
                "draft_recon_network": recon>>"network",
                "gapfiller_network": gapfiller>>"network"
            }

            self._build(
                processes = processes,
                connectors = connectors,
                interfaces = interfaces,
                outerfaces = outerfaces,
                user = user,
                **kwargs
            )

    # importers
    def get_ec_importer(self) -> ECImporter:
        return self._processes["ec_importer"]

    def get_biomass_importer(self) -> BiomassImporter:
        return self._processes["biomass_importer"]

    def get_medium_importer(self) -> MediumImporter:
        return self._processes["medium_importer"]

    # sources
    def get_ec_source(self) -> Source:
        return self._processes["ec_source"]

    def get_biomass_source(self) -> Source:
        return self._processes["biomass_source"]

    def get_medium_source(self) -> Source:
        return self._processes["medium_source"]

    # other procs
    def get_gapfiller(self) -> GapFiller:
        return self._processes["gapfiller"]

    def get_draft_recon(self) -> DraftRecon:
        return self._processes["draft_recon"]

    def get_sink(self) -> Sink:
        return self._processes["sink"]