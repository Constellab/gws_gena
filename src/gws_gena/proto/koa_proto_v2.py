
from gws_core import (ProcessSpec, Protocol,protocol_decorator)
from gws_gena.twin.twin_builder_v2 import TwinBuilderV2
from ..koa.koa_v2 import KOAV2


@protocol_decorator("KOAProtoV2", human_name="KOA protocol V2", short_description="KnockOut analysis protocol")
class KOAProtoV2(Protocol):

    def configure_protocol(self) -> None:
        twin_builder: ProcessSpec = self.add_process(TwinBuilderV2, 'twin_builder')
        koa: ProcessSpec = self.add_process(KOAV2, 'koa')

        self.add_connectors([
            (twin_builder >> "twin", koa << "twin")])

        self.add_interface('network', twin_builder, 'network')
        self.add_interface('context', twin_builder, 'context')

        self.add_interface('ko_table', koa, 'ko_table')

        self.add_outerface('twin', koa, 'twin')
        self.add_outerface('koa_result', koa, 'koa_result')
