
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, GTest, Settings
from gws_gena import Compound, Network, NetworkImporter, Reaction, Twin
from pandas import DataFrame

settings = Settings.get_instance()


class TestNetwork(BaseTestCaseUsingFullBiotaDB):

    def test_network_import_bigg_file(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "ecoli")
        file_path = os.path.join(data_dir, "ecoli.json")

        net = NetworkImporter.call(
            File(path=file_path),
            params=ConfigParams({"translate_ids": True})
        )

        self.print("ecoli successffuly imported - skip exchange reactions")
        self.assertEqual(len(net.compounds), 73)
        self.assertEqual(len(net.reactions), 74)

        with open(os.path.join(data_dir, './build/', 'ecoli_dump_with_conv.json'), 'w', encoding="utf-8") as fp:
            data = net.dumps()
            json.dump(data, fp, indent=4)

        # import 2
        net = NetworkImporter.call(
            File(path=file_path),
            params=ConfigParams({"translate_ids": True})
        )
        self.print("ecoli successffuly imported - skip exchange reactions")
        self.assertEqual(len(net.compounds), 73)
        self.assertEqual(len(net.reactions), 74)
