
from gws_core import ConfigParams, File, TabularView, resource_decorator, view, TypingStyle

from .view.network_view import NetworkView


@resource_decorator("NetworkFile", human_name="NetworkFile", short_description="Metabolic network file",
                    style=TypingStyle.material_icon(material_icon_name='hub', background_color='#F86104'))
class NetworkFile(File):

    @view(view_type=NetworkView, human_name="Network")
    def view_as_network(self, params: ConfigParams) -> NetworkView:
        """ View as network """
        from .network_task.network_importer import NetworkImporter
        net = NetworkImporter.call(self, {})
        return net.view_as_network(params)

    @view(view_type=TabularView, human_name="Reaction table")
    def view_as_table(self, params: ConfigParams) -> TabularView:
        """ View as table """
        from .network_task.network_importer import NetworkImporter
        net = NetworkImporter.call(self, {})
        return net.view_as_table(params)
