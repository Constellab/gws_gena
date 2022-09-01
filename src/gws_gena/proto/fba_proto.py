# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (FIFO2, ConfigParams, ProcessSpec, Protocol, Sink, Source,
                      protocol_decorator)

from ..fba.fba import FBA
from ..twin.twin_annotator import TwinAnnotator
from ..twin.twin_builder import TwinBuilder


@protocol_decorator("FBAProto", human_name="FBA protocol", short_description="Flux balance analysis protocol")
class FBAProto(Protocol):

    def configure_protocol(self) -> None:
        fba: ProcessSpec = self.add_process(FBA, 'fba')
        twin_builder: ProcessSpec = self.add_process(TwinBuilder, 'twin_builder').set_param("use_context", True)
        twin_annotator: ProcessSpec = self.add_process(TwinAnnotator, 'twin_annotator')

        self.add_connectors([
            (twin_builder >> "twin", fba << "twin"),
            (twin_builder >> "twin", twin_annotator << "twin"),
            (fba >> "result", twin_annotator << "fba_result")
        ])

        self.add_interface('network', twin_builder, 'network')
        self.add_interface('context', twin_builder, 'context')

        self.add_outerface('fba_result', fba, 'result')
        self.add_outerface('annotated_twin', twin_annotator, 'twin')
