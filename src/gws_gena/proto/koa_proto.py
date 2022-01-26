# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (FIFO2, ConfigParams, ProcessSpec, Protocol, Sink, Source,
                      protocol_decorator)

from ..koa.koa import KOA
from ..twin.twin_builder import TwinBuilder


@protocol_decorator("KOAProto", human_name="KOA protocol", short_description="KnockOut analysis protocol")
class KOAProto(Protocol):

    def configure_protocol(self, config_params: ConfigParams) -> None:
        twin_builder: ProcessSpec = self.add_process(TwinBuilder, 'twin_builder').set_param("use_context", True)
        koa: ProcessSpec = self.add_process(KOA, 'koa')

        self.add_connectors([
            (twin_builder >> "twin", koa << "twin")])

        self.add_interface('network', twin_builder, 'network')
        self.add_interface('context', twin_builder, 'context')
        self.add_interface('ko_table', koa, 'ko_table')
        self.add_outerface('ko_result', koa, 'result')
