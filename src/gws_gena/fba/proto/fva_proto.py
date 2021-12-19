# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math
import os

from gws_core import (FIFO2, ConfigParams, ProcessSpec, Protocol, Sink, Source,
                      protocol_decorator)

from ...network.network_task import NetworkImporter
from ...twin.twin_annotator import TwinAnnotator
from ...twin.twin_builder import TwinBuilder
from ...twin.twin_context_task import TwinContextImporter
from ..fva import FVA


@protocol_decorator("FVAProto")
class FVAProto(Protocol):

    def configure_protocol(self, config_params: ConfigParams) -> None:
        # network
        network_importer: ProcessSpec = self.add_process(NetworkImporter, 'network_importer')
        # context
        context_importer: ProcessSpec = self.add_process(TwinContextImporter, 'context_importer')
        # fva
        fva: ProcessSpec = self.add_process(FVA, 'fva')
        twin_builder: ProcessSpec = self.add_process(TwinBuilder, 'twin_builder').set_param("use_context", True)
        twin_annotator: ProcessSpec = self.add_process(TwinAnnotator, 'twin_annotator')

        self.add_connectors([
            (network_importer >> "target", twin_builder << "network"),
            (context_importer >> "target", twin_builder << "context"),
            (twin_builder >> "twin", fva << "twin"),
            (twin_builder >> "twin", twin_annotator << "twin"),
            (fva >> "result", twin_annotator << "fba_result")
        ])

        self.add_interface('network_file', network_importer, 'source')
        self.add_interface('context_file', context_importer, 'source')

        self.add_outerface('fva_result', fva, 'result')
        self.add_outerface('annotated_twin', twin_annotator, 'twin')
