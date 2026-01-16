import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File
from gws_gena import DataProvider, NetworkImporter


class TestNetwork(BaseTestCaseUsingFullBiotaDB):
    def test_network_import_bigg_file(self):
        data_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(data_dir, "ecoli")
        file_path = os.path.join(data_dir, "ecoli.json")

        net = NetworkImporter.call(File(path=file_path), params={"add_biomass": True})

        self.print("ecoli successffuly imported - skip exchange reactions")
        self.assertEqual(len(net.compounds), 73)
        self.assertEqual(len(net.reactions), 74)

        # with open(os.path.join(data_dir, './build/', 'ecoli_dump_with_conv.json'), 'w', encoding="utf-8") as fp:
        #     data = net.dumps()
        #     json.dump(data, fp, indent=4)

        # import 2
        net = NetworkImporter.call(File(path=file_path), params={"add_biomass": True})
        self.print("ecoli successffuly imported - skip exchange reactions")
        self.assertEqual(len(net.compounds), 73)
        self.assertEqual(len(net.reactions), 74)
