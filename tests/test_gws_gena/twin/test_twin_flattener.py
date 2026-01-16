
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings
from gws_gena import ContextImporter, NetworkImporter, Twin

settings = Settings.get_instance()


class TestTwinFlattener(BaseTestCaseUsingFullBiotaDB):

    def test_toy(self):
        self.print("Test Network Import")
        testdata_dir = settings.get_variable("gws_gena:testdata_dir")
        output_dir = os.path.join(testdata_dir, "flattener")
        data_dir = os.path.join(testdata_dir, "toy")

        file_path = os.path.join(data_dir, "toy.json")

        net = NetworkImporter.call(
            File(path=file_path),
            params={"skip_orphans": True,"add_biomass" : True}
        )

        file_path = os.path.join(data_dir, "toy_context.json")
        ctx = ContextImporter.call(
            File(path=file_path),
            params={}
        )

        twin = Twin()
        twin.add_network(net)
        twin.add_context(ctx, related_network=net)

        print(twin.dumps_flat())

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # with open(os.path.join(output_dir, "toy_flat.json"), 'w', encoding="utf-8") as fp:
        #     json.dump(twin.dumps_flat(), fp, indent=4)

        with open(os.path.join(output_dir, "toy_flat.json"), encoding="utf-8") as fp:
            expected_json = json.load(fp)

        self.assertEqual(twin.dumps_flat(), expected_json)
