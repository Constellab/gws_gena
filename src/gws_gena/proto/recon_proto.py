# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (FIFO2, ConfigParams, Interface, Outerface, ProcessSpec,
                      Protocol, Settings, Sink, Source, Task,
                      protocol_decorator)

from ..data.biomass_reaction_table_task import BiomassReactionTableImporter
from ..data.ec_table_task import ECTableImporter
from ..data.medium_table_task import MediumTableImporter
from ..recon.gap_filler import GapFiller
from ..recon.recon import DraftRecon


@protocol_decorator("ReconProto")
class ReconProto(Protocol):

    def configure_protocol(self, config_params: ConfigParams) -> None:
        # ec
        ec_importer: ProcessSpec = self.add_process(ECTableImporter, 'ec_importer')
        ec_importer.set_param("ec_column", "ec_number")
        # biomass
        biomass_importer: ProcessSpec = self.add_process(BiomassReactionTableImporter, 'biomass_importer')
        biomass_importer.set_param("biomass_column", "biomass")
        biomass_importer.set_param("chebi_column", "chebi_id")
        # medium
        medium_importer: ProcessSpec = self.add_process(MediumTableImporter, 'medium_importer')
        medium_importer.set_param("chebi_column", "chebi_id")
        # other procs
        recon: ProcessSpec = self.add_process(DraftRecon, 'recon')
        gap_filler: ProcessSpec = self.add_process(GapFiller, 'gap_filler')
        sink: ProcessSpec = self.add_process(Sink, 'sink')

        self.add_connectors([
            (ec_importer >> "target", recon << "ec_table"),
            (biomass_importer >> "target", recon << "biomass_table"),
            (medium_importer >> "target", recon << "medium_table"),
            (recon >> "network", gap_filler << "network"),
            (gap_filler >> "network", sink << "resource")
        ])

        # interface
        self.add_interface('ec_file', ec_importer, 'source')
        self.add_interface('biomass_file', biomass_importer, 'source')
        self.add_interface('medium_file', medium_importer, 'source')
        # outerface
        self.add_outerface('draft_recon_network', recon, 'network')
        self.add_outerface('gap_filler_network', gap_filler, 'network')
