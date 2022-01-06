# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (FIFO2, ConfigParams, ProcessSpec, Protocol, Sink, Source,
                      protocol_decorator)

from ..data.ec_table_task import ECTableExporter
from ..data.entity_id_table_task import EntityIDTableImporter
from ..koa.koa import KOA
from ..network.network_task import NetworkImporter
from ..twin.twin_builder import TwinBuilder
from ..twin.twin_context_task import TwinContextImporter


@protocol_decorator("KOAProto", short_description="Protocol for knockout analysis")
class KOAProto(Protocol):

    def configure_protocol(self, config_params: ConfigParams) -> None:
        # twin
        network_importer: ProcessSpec = self.add_process(NetworkImporter, 'network_importer')
        context_importer: ProcessSpec = self.add_process(TwinContextImporter, 'context_importer')
        twin_builder: ProcessSpec = self.add_process(TwinBuilder, 'twin_builder').set_param("use_context", True)
        # koa
        ko_table_importer: ProcessSpec = self.add_process(EntityIDTableImporter, 'ko_table_importer')
        koa: ProcessSpec = self.add_process(KOA, 'koa')

        self.add_connectors([
            (network_importer >> "target", twin_builder << "network"),
            (context_importer >> "target", twin_builder << "context"),
            (ko_table_importer >> "target", koa << "ko_table"),
            (twin_builder >> "twin", koa << "twin"),
        ])

        self.add_interface('network_file', network_importer, 'source')
        self.add_interface('context_file', context_importer, 'source')
        self.add_interface('ko_table_file', ko_table_importer, 'source')
        self.add_outerface('ko_result', koa, 'result')
