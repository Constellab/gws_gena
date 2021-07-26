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
from .biomodel import BioModel, BioModelBuilder
from .rnd_explore import RndExplorer

class RndExplorerProto(Protocol):
    
    def __init__(self, *args, user = None, **kwargs): 
        super().__init__(*args, user=user, **kwargs)
        if not self.is_built:
            biomodel_builder = BioModelBuilder()
            biomodel_builder.set_param("use_context", False)
            rnd_explorer = RndExplorer()
            rnd_explorer.set_param("least_energy_weight", 0.001)
            network_fifo = FIFO2()
            network_source = Source()
            network_importer = NetworkImporter()
            processes = {
                "network_fifo": network_fifo,
                "network_source": network_source,
                "network_importer": network_importer,
                "biomodel_builder": biomodel_builder,
                "rnd_explorer": rnd_explorer
            }
            connectors = [
                network_source>>"resource" | network_fifo<<"resource_1",
                network_importer>>"data" | network_fifo<<"resource_2",
                (network_fifo>>"resource").pipe(biomodel_builder<<"network", lazy=True),
                biomodel_builder>>"biomodel" | rnd_explorer<<"biomodel"
            ]
            interfaces = {
                "network_file": network_importer<<"file"
            }
            outerfaces = {
                "rnd_explorer_file": rnd_explorer>>"file"
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

    def get_rnd_explorer(self) -> RndExplorer:
        return self._processes["rnd_explorer"]