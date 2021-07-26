# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import math

from gws.protocol import Protocol
from gws.settings import Settings
from gws.plug import Source, Sink, FIFO2
from gws.io import Interface, Outerface
from gws.file import *

from .network import NetworkImporter
from .context import ContextImporter
from .biomodel import BioModel, BioModelBuilder
from .fast_fva import FastFVA
from .annotator import BioModelAnnotator

class FastFVAProto(Protocol):
    
    def __init__(self, *args, user = None, **kwargs): 
        super().__init__(*args, user=user, **kwargs)
        if not self.is_built:
            biomodel_builder = BioModelBuilder()
            biomodel_builder.set_param("use_context", True)
            fva = FastFVA()
            network_fifo = FIFO2()
            network_source = Source()
            network_importer = NetworkImporter()
            context_fifo = FIFO2()
            context_source = Source()
            context_importer = ContextImporter()
            biomodel_annotator = BioModelAnnotator()
            processes = {
                "network_fifo": network_fifo,
                "network_source": network_source,
                "network_importer": network_importer,
                "context_fifo": context_fifo,
                "context_source": context_source,
                "context_importer": context_importer,
                "biomodel_builder": biomodel_builder,
                "fva": fva,
                "biomodel_annotator": biomodel_annotator
            }
            connectors = [
                network_source>>"resource" | network_fifo<<"resource_1",
                network_importer>>"data" | network_fifo<<"resource_2",
                (network_fifo>>"resource").pipe(biomodel_builder<<"network", lazy=True),
                context_source>>"resource" | context_fifo<<"resource_1",
                context_importer>>"data" | context_fifo<<"resource_2",
                (context_fifo>>"resource").pipe(biomodel_builder<<"context", lazy=True),
                biomodel_builder>>"biomodel" | fva<<"biomodel",
                biomodel_builder>>"biomodel" | biomodel_annotator<<"biomodel",
                fva>>"result" | biomodel_annotator<<"fba_result",
            ]
            interfaces = {
                "network_file": network_importer<<"file",
                "context_file": context_importer<<"file"
            }
            outerfaces = {
                "fva_result": fva>>"result",
                "annotated_biomodel": biomodel_annotator>>"biomodel"
            }
            self._build(
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

    def get_fva(self) -> FastFVA:
        return self._processes["fva"]