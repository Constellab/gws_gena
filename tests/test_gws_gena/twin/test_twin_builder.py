import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings, TaskRunner
from gws_gena import ContextImporter, DataProvider, NetworkImporter, Twin, TwinBuilder

settings = Settings.get_instance()


class TestTwinBuilder(BaseTestCaseUsingFullBiotaDB):
    def test_twin_builder(self):
        self.print("Test Twin")
        data_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(data_dir, "small_net")

        file_path = os.path.join(data_dir, "small_net.json")
        net = NetworkImporter.call(File(path=file_path), params={"add_biomass": True})
        file_path = os.path.join(data_dir, "small_context.json")
        ctx = ContextImporter.call(File(path=file_path), params={})

        twin = Twin()
        twin.add_network(net)
        twin.add_context(ctx, related_network=net)

        tester = TaskRunner(
            params={}, inputs={"network": net, "context": ctx}, task_type=TwinBuilder
        )
        outputs = tester.run()

        twin = outputs["twin"]

        self.print(str(twin.networks))
        self.print(str(twin))
