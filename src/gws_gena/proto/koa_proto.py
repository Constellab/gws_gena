
from gws_core import (ProcessSpec, Protocol,protocol_decorator)

from ..koa.koa import KOA
from ..twin.twin_builder import TwinBuilder


@protocol_decorator("KOAProto", human_name="KOA protocol", short_description="KnockOut analysis protocol")
class KOAProto(Protocol):

    def configure_protocol(self) -> None:
        twin_builder: ProcessSpec = self.add_process(TwinBuilder, 'twin_builder')
        koa: ProcessSpec = self.add_process(KOA, 'koa')

        self.add_connectors([
            (twin_builder >> "twin", koa << "twin")])

        self.add_interface('network', twin_builder, 'network')
        self.add_interface('context', twin_builder, 'context')

        self.add_interface('ko_table', koa, 'ko_table')

        self.add_outerface('twin', koa, 'twin')
        self.add_outerface('koa_result', koa, 'koa_result')
