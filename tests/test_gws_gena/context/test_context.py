import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File
from gws_gena import ContextImporter, DataProvider


class TestContext(BaseTestCaseUsingFullBiotaDB):
    def test_context(self):
        data_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(data_dir, "toy")
        file_path = os.path.join(data_dir, "toy_context.json")
        ctx = ContextImporter.call(File(path=file_path), params={})

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        self.print(ctx.dumps())

        self.assertEqual(data["reaction_data"][1], ctx.dumps()["reaction_data"][1])
        self.assertEqual(data["reaction_data"][0].get("confidence_score"), [1.0])
        self.assertEqual(ctx.dumps()["reaction_data"][0].get("confidence_score"), [1.0])

        ctx2 = ctx.copy()
        self.assertEqual(ctx2.dumps(), ctx.dumps())
