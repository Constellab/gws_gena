# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import math

from gws.logger import Error, Info
from gws.model import Protocol
from gws.settings import Settings
from gws.plug import Source, Sink, FIFO2
from gws.io import Interface, Outerface
from gws.file import *

from gena.network import NetworkImporter
from gena.context import ContextImporter
from gena.biomodel import BioModel, BioModelBuilder
from gena.fba import FluxAnalyzer

class FluxAnalyzerProto(Protocol):
    
    def __init__(self, *args, user = None, **kwargs): 
        biomodel_builder = BioModelBuilder()
        biomodel_builder.set_param("use_context", True)
        
        flux_analyzer = FluxAnalyzer()
        flux_analyzer.set_param("least_energy_weight", 0.001)
        
        network_fifo = FIFO2()
        network_source = Source()
        network_importer = NetworkImporter()

        context_fifo = FIFO2()
        context_source = Source()
        context_importer = ContextImporter()

        processes = {
            "network_fifo": network_fifo,
            "network_source": network_source,
            "network_importer": network_importer,
            "context_fifo": context_fifo,
            "context_source": context_source,
            "context_importer": context_importer,
            "biomodel_builder": biomodel_builder,
            "flux_analyzer": flux_analyzer
        }

        connectors = [
            network_source>>"resource" | network_fifo<<"resource_1",
            network_importer>>"data" | network_fifo<<"resource_2",
            (network_fifo>>"resource").pipe(biomodel_builder<<"network", lazy=True),
            biomodel_builder>>"biomodel" | flux_analyzer<<"biomodel"
        ]
        
        interfaces = {
            "network_file": network_importer<<"file",
            "context_file": context_importer<<"file"
        }

        outerfaces = {
            "flux_analyzer_file": flux_analyzer>>"file"
        }

        super().__init__(
            processes = processes,
            connectors = connectors,
            interfaces = interfaces,
            outerfaces = outerfaces,
            user = user,
            **kwargs
        )

    # process
    def get_network_importer(self) -> NetworkImporter:
        return self._processes["network_importer"]

    def get_biomodel_builder(self) -> BioModelBuilder:
        return self._processes["biomodel_builder"]

    def get_flux_analyzer(self) -> FluxChecker:
        return self._processes["flux_analyzer"]