

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
    DEFAULT_NAME = "twin"

    NETWORK_NAME = "network"
    CONTEXT_NAME = "context"

    def __init__(self):
        super().__init__()
        if not self.name:
            self.name = self.DEFAULT_NAME

    def set_network(self, network: NetworkCobra) -> None:
        """
        Set a network to the twin

        :param network: The network to add
        :type network: `gena.network.NetworkCobra`
        """
        if not isinstance(network, NetworkCobra):
            raise Exception("The network must an instance of Network")
        if self.resource_exists(network.name):
            raise Exception(f"Network name '{network.name}' duplicated")

        self.add_resource(network, self.NETWORK_NAME)

    def get_network(self) -> NetworkCobra:
        return self.get_resource(self.NETWORK_NAME)

    def set_context(self, context: Context) -> None:
        """
        Set a context to the twin

        :param context: The context to add
        :type context: `gena.context.Context`
        """
        if not isinstance(context, Context):
            raise Exception("The context must be an instance of Context")
        if self.resource_exists(context.name):
            raise Exception(f'The context "{context.name}" duplicate')

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
