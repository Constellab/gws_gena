
from gws_core import ProcessSpec, Protocol, protocol_decorator

from ..fva.fva import FVA
from ..twin.twin_builder import TwinBuilder


@protocol_decorator("FVAProto", human_name="FVA protocol", short_description="Flux variability analysis protocol")
class FVAProto(Protocol):
    """
    Protocol that wrapped the Twin builder and the FVA Tasks.

    You can unfold this protocol to see these Tasks and the associated documentation.

    You can also set the parameters directly from the dashboard of the protocol.
    """

    def configure_protocol(self) -> None:
        # fva
        fva: ProcessSpec = self.add_process(FVA, 'fva')
        twin_builder: ProcessSpec = self.add_process(TwinBuilder, 'twin_builder')

        self.add_connectors([
            (twin_builder >> "twin", fva << "twin"),
        ])

        self.add_interface('network', twin_builder, 'network')
        self.add_interface('context', twin_builder, 'context')

        self.add_outerface('fva_result', fva, 'fva_result')
        self.add_outerface('twin', fva, 'twin')
