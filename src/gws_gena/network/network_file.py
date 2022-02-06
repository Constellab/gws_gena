# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BadRequestException, BoolParam, ConfigParams, DictRField,
                      File, JSONFile, JSONView, Resource, ResourceExporter,
                      RField, StrRField, Table, TabularView,
                      resource_decorator, view)

from .view.network_view import NetworkView


@resource_decorator("NetworkFile",
                    human_name="NetworkFile",
                    short_description="Metabolic network file")
class NetworkFile(JSONFile):

    @view(view_type=NetworkView, human_name="Network")
    def view_as_network(self, params: ConfigParams) -> NetworkView:
        from .network_task import NetworkImporter
        net = NetworkImporter.call(self, {})
        return net.view_as_network(params)

    @view(view_type=TabularView, default_view=True, human_name="Reaction table")
    def view_as_table(self, params: ConfigParams) -> TabularView:
        from .network_task import NetworkImporter
        net = NetworkImporter.call(self, {})
        return net.view_as_table(params)
