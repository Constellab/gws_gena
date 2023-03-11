# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import ProcessSpec, Protocol, protocol_decorator

from ...recon.deprecated.recon_deprecated_000 import DraftRecon000
from ...sanitizer.gap.gap_filler import GapFiller


@protocol_decorator("ReconProto", human_name="Recon protocol",
                    short_description="Protocol for metabolic network reconstruction", deprecated_since="0.5.0",
                    deprecated_message="Please reconsider to use the latest version of ReconProto")
class ReconProto000(Protocol):
    """ ReconProto """

    def configure_protocol(self) -> None:
        recon: ProcessSpec = self.add_process(DraftRecon000, 'recon')
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
