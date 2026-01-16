import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, TaskRunner
from gws_gena import DataProvider, IsolateFinder, NetworkImporter


class TestIsolateFinder(BaseTestCaseUsingFullBiotaDB):
    def test_isolate_finder_ecoli(self):
        data_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(data_dir, "ecoli")

        net = NetworkImporter.call(
            File(path=os.path.join(data_dir, "ecoli.json")), {"add_biomass": True}
        )

        tester = TaskRunner(params={}, inputs={"network": net}, task_type=IsolateFinder)
        outputs = tester.run()
        result = outputs["result"]

        self.assertEqual(result.get_reaction_table().nb_rows, 0)
        self.assertEqual(result.get_compound_table().nb_rows, 0)

    def test_isolate_finder_pcys(self):
        data_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(data_dir, "pcys")

        net = NetworkImporter.call(
            File(path=os.path.join(data_dir, "pcys.json")), {"add_biomass": True}
        )

        tester = TaskRunner(params={}, inputs={"network": net}, task_type=IsolateFinder)
        outputs = tester.run()
        result = outputs["result"]

        self.assertEqual(result.get_reaction_table().nb_rows, 105)
        self.assertEqual(result.get_compound_table().nb_rows, 211)

        self.print(result.get_compound_table())

        self.print(result.get_reaction_table())
