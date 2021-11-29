# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import math

from gws_core import Protocol, Task, protocol_decorator, ConfigParams, ProcessSpec
from gws_core import Settings, Source, Sink, FIFO2, Interface, Outerface

from ...data.biomass_table import BiomassImporter
from ...data.medium_table import MediumImporter
from ...data.ec_table import ECTableImporter
from ..recon import DraftRecon
from ..gap_filler import GapFiller


@protocol_decorator("ReconProto")
class ReconProto(Protocol):

    def configure_protocol(self, config_params: ConfigParams) -> None:
        # ec
        ec_importer: ProcessSpec = self.add_process(ECTableImporter, 'ec_importer')
        ec_importer.set_param("ec_column", "EC Number")
        # biomass
        biomass_importer: ProcessSpec = self.add_process(BiomassImporter, 'biomass_importer')
        biomass_importer.set_param("biomass_column", "Biomass")
        biomass_importer.set_param("chebi_column", "Chebi ID")
        # medium
        medium_importer: ProcessSpec = self.add_process(MediumImporter, 'medium_importer')
        medium_importer.set_param("chebi_column", "Chebi ID")
        # other procs
        recon: ProcessSpec = self.add_process(DraftRecon, 'recon')
        gap_filler: ProcessSpec = self.add_process(GapFiller, 'gap_filler')
        sink: ProcessSpec = self.add_process(Sink, 'sink')

        self.add_connectors([
            (ec_importer >> "resource", recon << "ec_table"),
            (biomass_importer >> "resource", recon << "biomass_table"),
            (medium_importer >> "resource", recon << "medium_table"),
            (recon >> "network", gap_filler << "network"),
            (gap_filler >> "network", sink << "resource")
        ])

        # interface
        self.add_interface('ec_file', ec_importer, 'file')
        self.add_interface('biomass_file', biomass_importer, 'file')
        self.add_interface('medium_file', medium_importer, 'file')
        # outerface
        self.add_outerface('draft_recon_network', recon, 'network')
        self.add_outerface('gap_filler_network', gap_filler, 'network')
