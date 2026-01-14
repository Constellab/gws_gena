from gws_core import ConfigParams, File, TabularView, TypingStyle, resource_decorator, view

from .view.network_view import NetworkView


@resource_decorator(
    "NetworkFile",
    human_name="NetworkFile",
    short_description="Metabolic network file",
    style=TypingStyle.material_icon(material_icon_name="hub", background_color="#F86104"),
)
class NetworkFile(File):
    @view(view_type=NetworkView, human_name="Network")
    def view_as_network(self, params: ConfigParams) -> NetworkView:
        from .network_task.network_importer import NetworkImporter

        """View as network"""
        net = NetworkImporter.call(self, {})
        return net.view_as_network(params)

    @view(view_type=TabularView, human_name="Reaction table")
    def view_as_table(self, params: ConfigParams) -> TabularView:
        from .network_task.network_importer import NetworkImporter

        """View as table"""
        net = NetworkImporter.call(self, {})
        return net.view_as_table(params)
