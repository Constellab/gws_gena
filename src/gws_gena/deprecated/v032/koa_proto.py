# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (FIFO2, ConfigParams, ProcessSpec, Protocol, Sink, Source,
                      protocol_decorator)

from ...twin.twin_builder import TwinBuilder
from .dep_koa.koa import KOA


@task_decorator("KOAProto_001", human_name="Deprecated KOA protocol",
                short_description="Knockout analysis protocol", hide=True, deprecated_since='0.4.0',
                deprecated_message="Use new version of KOAProto")
class KOAProto(Protocol):

    def configure_protocol(self) -> None:
        twin_builder: ProcessSpec = self.add_process(TwinBuilder, 'twin_builder').set_param("use_context", True)
        koa: ProcessSpec = self.add_process(KOA, 'koa')

        self.add_connectors([
            (twin_builder >> "twin", koa << "twin")])

        self.add_interface('network', twin_builder, 'network')
        self.add_interface('context', twin_builder, 'context')
        self.add_interface('ko_table', koa, 'ko_table')
        self.add_outerface('ko_result', koa, 'result')
