
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, Settings, TaskRunner
from gws_gena import ContextImporter, NetworkImporter, Twin, TwinBuilder

settings = Settings.get_instance()


class TestTwinBuilder(BaseTestCaseUsingFullBiotaDB):

    def test_twin_builder(self):
        self.print("Test Twin")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "small_net")

        file_path = os.path.join(data_dir, "small_net.json")
        net = NetworkImporter.call(
            File(path=file_path),
            params=ConfigParams()
        )
        file_path = os.path.join(data_dir, "small_context.json")
        ctx = ContextImporter.call(
            File(path=file_path),
            params=ConfigParams()
        )

        twin = Twin()
        twin.add_network(net)
        twin.add_context(ctx, related_network=net)

        tester = TaskRunner(
            params={},
            inputs={"network": net, "context": ctx},
            task_type=TwinBuilder
        )
        outputs = tester.run()

        twin = outputs["twin"]

        print(twin.networks)
        print(twin)
