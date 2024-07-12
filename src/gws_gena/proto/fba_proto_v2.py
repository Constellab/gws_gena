
from gws_core import ProcessSpec, Protocol, protocol_decorator

from gws_gena.network_v2.fba_v2 import FBAV2
from gws_gena.twin.twin_builder_v2 import TwinBuilderV2


@protocol_decorator("FBAProtoV2", human_name="FBA protocol V2", short_description="Flux balance analysis protocol")
class FBAProtoV2(Protocol):

    """
    Protocol that wrapped the Twin builder and the FBA Tasks.

    You can unfold this protocol to see these Tasks and the associated documentation.

    You can also set the parameters directly from the dashboard of the protocol.
    """

    def configure_protocol(self) -> None:
        fba: ProcessSpec = self.add_process(FBAV2, 'fba')
        twin_builder: ProcessSpec = self.add_process(TwinBuilderV2, 'twin_builder')

        self.add_connectors([
            (twin_builder >> "twin", fba << "twin"),
        ])

        self.add_interface('network', twin_builder, 'network')
        self.add_interface('context', twin_builder, 'context')

        self.add_outerface('fba_result', fba, 'fba_result')
        self.add_outerface('twin', fba, 'twin')
