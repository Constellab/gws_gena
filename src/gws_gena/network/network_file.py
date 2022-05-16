# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import ConfigParams, File, TabularView, resource_decorator, view

from .view.network_view import NetworkView


@resource_decorator("NetworkFile",
                    human_name="NetworkFile",
                    short_description="Metabolic network file")
class NetworkFile(File):

    @view(view_type=NetworkView, default_view=True, human_name="Network")
    def view_as_network(self, params: ConfigParams) -> NetworkView:
        """ View as network """
        from .network_tasks.network_importer import NetworkImporter
        net = NetworkImporter.call(self, {})
        return net.view_as_network(params)

    @view(view_type=TabularView, human_name="Reaction table")
    def view_as_table(self, params: ConfigParams) -> TabularView:
        """ View as table """
        from .network_tasks.network_importer import NetworkImporter
        net = NetworkImporter.call(self, {})
        return net.view_as_table(params)
