# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (FIFO2, ConfigParams, ProcessSpec, Protocol, Sink, Source,
                      protocol_decorator)

from ..fva.fva import FVA
from ..twin.twin_annotator import TwinAnnotator
from ..twin.twin_builder import TwinBuilder


@protocol_decorator("FVAProto_002", human_name="FVA protocol", short_description="Flux variability analysis protocol")
class FVAProto(Protocol):

    def configure_protocol(self) -> None:
        # fva
        fva: ProcessSpec = self.add_process(FVA, 'fva')
        twin_builder: ProcessSpec = self.add_process(TwinBuilder, 'twin_builder').set_param("use_context", True)
        twin_annotator: ProcessSpec = self.add_process(TwinAnnotator, 'twin_annotator')

        self.add_connectors([
            (twin_builder >> "twin", fva << "twin"),
            (twin_builder >> "twin", twin_annotator << "twin"),
            (fva >> "result", twin_annotator << "fba_result")
        ])

        self.add_interface('network', twin_builder, 'network')
        self.add_interface('context', twin_builder, 'context')

        self.add_outerface('fva_result', fva, 'result')
        self.add_outerface('annotated_twin', twin_annotator, 'twin')
