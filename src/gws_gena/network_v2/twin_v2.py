

from gws_core import ResourceSet, TypingStyle, resource_decorator
from gws_gena.network_v2.network_cobra import NetworkCobra

from ..context.context import Context


@resource_decorator("TwinV2", human_name="TwinV2", short_description="Twin of cell metabolism",
                    style=TypingStyle.material_icon(material_icon_name='hub', background_color='#FFA122'))
class TwinV2(ResourceSet):
    """
    Class that represents a twin.

    A twin is defined by a set of networks related to a set of contexts. It
    can therefore be used for simulation and prediction.
    """
    DEFAUTL_NAME = "twin"

    NETWORK_NAME = "network"
    CONTEXT_NAME = "context"

    def __init__(self):
        super().__init__()
        if not self.name:
            self.name = self.DEFAUTL_NAME

    def set_network(self, network: NetworkCobra) -> None:
        self.add_resource(network, self.NETWORK_NAME)

    def get_network(self) -> NetworkCobra:
        return self.get_resource(self.NETWORK_NAME)

    def set_context(self, context: Context) -> None:
        self.add_resource(context, self.CONTEXT_NAME)

    def get_context(self) -> Context:
        return self.get_resource(self.CONTEXT_NAME)

    def copy(self):
        twin = TwinV2()
        twin.set_network(self.get_network())
        twin.set_context(self.get_context())
        return twin

    # @view(view_type=JSONView, human_name="Summary")
    # def view_as_summary(self, _: ConfigParams) -> JSONView:
    #     """ view as summary """
    #     data = self.get_summary()
    #     j_view = JSONView()
    #     j_view.set_data(data)
    #     return j_view
