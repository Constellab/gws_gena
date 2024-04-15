
from gws_core import ProcessSpec, Protocol, protocol_decorator

from ..fba.fba import FBA
from ..twin.twin_builder import TwinBuilder


@protocol_decorator("FBAProto", human_name="FBA protocol", short_description="Flux balance analysis protocol")
class FBAProto(Protocol):

    """
    Protocol that wrapped the Twin builder and the FBA Tasks.

    You can unfold this protocol to see these Tasks and the associated documentation.

    You can also set the parameters directly from the dashboard of the protocol.
    """

    def configure_protocol(self) -> None:
        fba: ProcessSpec = self.add_process(FBA, 'fba')
        twin_builder: ProcessSpec = self.add_process(TwinBuilder, 'twin_builder')

        self.add_connectors([
            (twin_builder >> "twin", fba << "twin"),
        ])

        self.add_interface('network', twin_builder, 'network')
        self.add_interface('context', twin_builder, 'context')

        self.add_outerface('fba_result', fba, 'fba_result')
        self.add_outerface('twin', fba, 'twin')
