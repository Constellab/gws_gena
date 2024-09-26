
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings
from gws_gena.network.network_task.network_exporter_v2 import NetworkExporterV2
from gws_gena.network.network_task.network_importer_v2 import NetworkImporterV2

settings = Settings.get_instance()


class TestNetworkExporter(BaseTestCaseUsingFullBiotaDB):

    def test_network_import(self):
        self.print("Test Network Exporter with small_net")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "small_net")

        file_path = os.path.join(data_dir, "small_net_v2.json")

        net = NetworkImporterV2.call(File(path=file_path))

        ## CASE JSON exporter ##
        self.print("Test json export")

        file_exporter = NetworkExporterV2.call(
            net,
            params={'file_name': "network",
                    'file_format': "json"}
        )
        self.print("après exporter")

        self.assertTrue(file_exporter.is_json())

        self.print("Test Network Exporter with ecoli with metabolite biomass")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "ecoli")

        file_path = os.path.join(data_dir, "ecoli_with_biomass_metabolite.json")

        net = NetworkImporterV2.call(File(path=file_path))

        ## CASE JSON exporter ##
        self.print("Test json export")

        file_exporter = NetworkExporterV2.call(
            net,
            params={'file_name': "network",
                    'file_format': "json"}
        )

        self.assertTrue(file_exporter.is_json())
