
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings
from gws_gena import NetworkImporter
from gws_gena.network.graph.graph import Graph

settings = Settings.get_instance()


class TestGraph(BaseTestCaseUsingFullBiotaDB):

    def test_graph(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")
        file_path = os.path.join(data_dir, "toy.json")

        net = NetworkImporter.call(
            File(path=file_path),
            params={"skip_orphans": True,
                    "add_biomass" : True}
        )

        graph = Graph(net)

        nodes = graph.find_neigbors(["X2_c"])
        self.assertTrue('X2_c' in nodes)
        self.assertTrue('X2_e' in nodes)
        self.assertTrue('X1_c' in nodes)
        print(nodes)
