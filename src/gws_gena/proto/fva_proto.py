# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import ProcessSpec, Protocol, protocol_decorator

from ..fva.fva import FVA
from ..twin.twin_builder import TwinBuilder


@protocol_decorator("FVAProto", human_name="FVA protocol", short_description="Flux variability analysis protocol")
class FVAProto(Protocol):

    def configure_protocol(self) -> None:
        # fva
        fva: ProcessSpec = self.add_process(FVA, 'fva')
        twin_builder: ProcessSpec = self.add_process(TwinBuilder, 'twin_builder').set_param("use_context", True)

        self.add_connectors([
            (twin_builder >> "twin", fva << "twin"),
        ])

        self.add_interface('network', twin_builder, 'network')
        self.add_interface('context', twin_builder, 'context')

        self.add_outerface('fva_result', fva, 'fva_result')
        self.add_outerface('twin', fva, 'twin')
