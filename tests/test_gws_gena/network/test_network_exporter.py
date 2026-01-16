import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File
from gws_gena import DataProvider, NetworkExporter, NetworkImporter


class TestNetworkExporter(BaseTestCaseUsingFullBiotaDB):
    def test_network_import(self):
        self.print("Test Network Exporter with small_net")
        data_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(data_dir, "small_net")

        file_path = os.path.join(data_dir, "small_net.json")

        net = NetworkImporter.call(File(path=file_path), params={"add_biomass": True})

        ## CASE JSON exporter ##
        self.print("Test json export")

        file_exporter = NetworkExporter.call(
            net, params={"file_name": "network", "file_format": "json"}
        )

        self.assertTrue(file_exporter.is_json())

        ## CASE csv exporter ##
        self.print("Test csv export")

        file_exporter = NetworkExporter.call(
            net, params={"file_name": "network", "file_format": "csv"}
        )

        self.assertTrue(file_exporter.is_csv())

        ## CASE txt exporter ##
        self.print("Test txt export")

        file_exporter = NetworkExporter.call(
            net, params={"file_name": "network", "file_format": "txt"}
        )

        self.assertTrue(file_exporter.is_txt())

        self.print("Test Network Exporter with ecoli with metabolite biomass")
        data_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(data_dir, "ecoli")

        file_path = os.path.join(data_dir, "ecoli_with_biomass_metabolite.json")

        net = NetworkImporter.call(
            File(path=file_path),
            params={"add_biomass": False, "biomass_metabolite_id_user": "biomass_biomass"},
        )

        ## CASE JSON exporter ##
        self.print("Test json export")

        file_exporter = NetworkExporter.call(
            net, params={"file_name": "network", "file_format": "json"}
        )

        self.assertTrue(file_exporter.is_json())

        ## CASE csv exporter ##
        self.print("Test csv export")

        file_exporter = NetworkExporter.call(
            net, params={"file_name": "network", "file_format": "csv"}
        )

        self.assertTrue(file_exporter.is_csv())

        ## CASE txt exporter ##
        self.print("Test txt export")

        file_exporter = NetworkExporter.call(
            net, params={"file_name": "network", "file_format": "txt"}
        )

        self.assertTrue(file_exporter.is_txt())
