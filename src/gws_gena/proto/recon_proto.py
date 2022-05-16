# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (FIFO2, ConfigParams, Interface, Outerface, ProcessSpec,
                      Protocol, Settings, Source, Task, protocol_decorator)

from ..data.biomass_reaction_table_task import BiomassReactionTableImporter
from ..data.ec_table_task import ECTableImporter
from ..data.medium_table_task import MediumTableImporter
from ..recon.gap_filler import GapFiller
from ..recon.recon import DraftRecon


@protocol_decorator("ReconProto", human_name="Recon protocol", short_description="Metabolic reconstruction protocol")
class ReconProto(Protocol):

    def configure_protocol(self) -> None:
        recon: ProcessSpec = self.add_process(DraftRecon, 'recon')
        gap_filler: ProcessSpec = self.add_process(GapFiller, 'gap_filler')

        self.add_connectors([
            (recon >> "network", gap_filler << "network"),
        ])

        # interface
        self.add_interface('ec_table', recon, 'ec_table')
        self.add_interface('biomass_table', recon, 'biomass_table')
        self.add_interface('medium_table', recon, 'medium_table')
        # outerface
        self.add_outerface('draft_recon_network', recon, 'network')
        self.add_outerface('gap_filler_network', gap_filler, 'network')
