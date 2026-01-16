import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, TaskRunner
from gws_gena import ContextImporter, DataProvider, NetworkImporter, Twin, TwinBuilder


class TestTwinImporter(BaseTestCaseUsingFullBiotaDB):
    def test_twin_importer(self):
        self.print("Test Task Twin importer")
        data_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(data_dir, "small_net")

        file_path = os.path.join(data_dir, "small_net.json")
        net = NetworkImporter.call(
            File(path=file_path), params={"skip_orphans": True, "add_biomass": True}
        )

        file_path = os.path.join(data_dir, "small_context.json")
        ctx = ContextImporter.call(File(path=file_path), params={})

        runner = TaskRunner(task_type=TwinBuilder, inputs={"network": net, "context": ctx})

        outputs = runner.run()
        twin = outputs["twin"]

        self.assertIsInstance(twin, Twin)
