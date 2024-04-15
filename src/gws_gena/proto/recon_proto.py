
from gws_core import ProcessSpec, Protocol, protocol_decorator

from ..recon.recon import DraftRecon
from ..sanitizer.gap.gap_filler import GapFiller


@protocol_decorator("ReconProto001", human_name="Recon protocol",
                    short_description="Protocol for metabolic network reconstruction")
class ReconProto(Protocol):
    """ ReconProto """

    def configure_protocol(self) -> None:
        recon: ProcessSpec = self.add_process(DraftRecon, 'recon')
        gap_filler: ProcessSpec = self.add_process(GapFiller, 'gap_filler')

        self.add_connectors([
            (recon >> "network", gap_filler << "network"),
        ])

        # interface
        self.add_interface('ec_table', recon, 'ec_table')
        self.add_interface('biomass_table', recon, 'biomass_table')
        # outerface
        self.add_outerface('draft_recon_network', recon, 'network')
        self.add_outerface('gap_filler_network', gap_filler, 'network')
