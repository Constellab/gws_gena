import os

from gws_core import BaseTestCase, File, Settings, TaskRunner
from gws_gena import DataProvider, NetworkMergem

settings = Settings.get_instance()


class TestMergem(BaseTestCase):
    def test_mergem(self):
        self.print("Test Mergem")

        data_dir = DataProvider.get_test_data_dir()
        file1 = File(path=os.path.join(data_dir, "ecoli", "ecoli.json"))
        file2 = File(path=os.path.join(data_dir, "ecoli", "ecoli.json"))

        tester = TaskRunner(
            params={"add_biomass": True},
            inputs={"network_1": file1, "network_2": file2},
            task_type=NetworkMergem,
        )
        outputs = tester.run()
        net_merged = outputs["network"]

        self.assertTrue("PDH" in str(net_merged.reactions))
        self.assertTrue("merged-objectives" in str(net_merged.reactions))
