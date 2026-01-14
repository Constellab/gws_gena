import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings, TaskRunner
from gws_gena import DataProvider, GapFiller, GapFinderHelper, NetworkImporter
from gws_gena.network.network import Network

settings = Settings.get_instance()


class TestGapFinder(BaseTestCaseUsingFullBiotaDB):
    def test_gap_filler_with_no_gaps(self):
        data_dir = DataProvider.get_test_data_dir()
        file_path = os.path.join(data_dir, "./ecoli/gaps/ecoli_without_SUCOAS.json")
        net = NetworkImporter.call(File(path=file_path), {"add_biomass": True})

        # params = {"tax_id":  "562"}  # ecoli
        params = {"tax_id": "2"}  # bacteria

        tester = TaskRunner(params=params, inputs={"network": net}, task_type=GapFiller)
        outputs = tester.run()

        # test results
        result: Network = outputs["network"]

        helper = GapFinderHelper()
        dead = helper.find_deadend_compound_ids(result)
        self.print(f"After gap filling: {len(dead)} dead-ends")
