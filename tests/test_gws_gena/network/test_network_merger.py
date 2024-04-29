
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import (ConfigParams, Experiment, File,
                      Settings, TaskRunner)
from gws_gena import Context, Network, NetworkImporter, NetworkMerger, Twin

settings = Settings.get_instance()


class TestMerge(BaseTestCaseUsingFullBiotaDB):

    def test_merger(self):
        self.print("Test Merger")

        data_dir = settings.get_variable("gws_gena:testdata_dir")
        file1 = File(path=os.path.join(data_dir, "network_merger", "net1.json"))
        file2 = File(path=os.path.join(data_dir, "network_merger", "net2.json"))

        net1 = NetworkImporter.call(file1, {"add_biomass" : True})
        net2 = NetworkImporter.call(file2, {"add_biomass" : True})
        n1 = len(net1.reactions)
        n2 = len(net2.reactions)

        tester = TaskRunner(
            params={},
            inputs={"network_1": net1, "network_2": net2},
            task_type=NetworkMerger
        )
        outputs = tester.run()
        net_merged = outputs["network"]

        n_total = len(net_merged.reactions)
        self.assertEqual(n_total, n1+n2)

        self.assertTrue("RHEA_66592_4_2_99_18" in net_merged.reactions)
        self.assertTrue("RHEA_64596_2_4_1_370" in net_merged.reactions)

        self.assertTrue("RHEA_66592_4_2_99_18" in net2.reactions)
        self.assertTrue("RHEA_64596_2_4_1_370" in net2.reactions)

        self.assertTrue("RHEA_66592_4_2_99_18" not in net1.reactions)
        self.assertTrue("RHEA_64596_2_4_1_370" not in net1.reactions)

        for _id in net1.reactions:
            self.assertTrue(_id in net_merged.reactions)
        for _id in net2.reactions:
            self.assertTrue(_id in net_merged.reactions)

        # file_name = "merger"
        # file_path = os.path.join(result_dir, file_name+"_net.csv")
        # with open(file_path, 'w', encoding="utf-8") as f:
        #     f.write(net_merged.to_csv())

        # file_path = os.path.join(result_dir, file_name+"_net.json")
        # with open(file_path, 'w', encoding="utf-8") as f:
        #     json.dump(net_merged.dumps(), f)

        # file_path = os.path.join(result_dir, file_name+"_stats.csv")
        # with open(file_path, 'w', encoding="utf-8") as f:
        #     table = net_merged.get_compound_stats_as_table()
        #     f.write(table.to_csv())
