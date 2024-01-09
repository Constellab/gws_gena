
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_biota import Compound as BiotaCompound
from gws_core import (ConfigParams, Experiment, ExperimentService, File, GTest,
                      Settings, TaskRunner)
from gws_gena import (Compound, Context, ContextBuilder, ContextImporter,
                      FluxTable, FluxTableImporter, Network, NetworkImporter,
                      Reaction, Twin)

settings = Settings.get_instance()


class TestContext(BaseTestCaseUsingFullBiotaDB):

    def test_context(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")
        file_path = os.path.join(data_dir, "toy_context.json")
        ctx = ContextImporter.call(File(path=file_path), params=ConfigParams())

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(ctx.dumps())

        self.assertEqual(data["measures"][1], ctx.dumps()["measures"][1])
        self.assertEqual(data["measures"][0].get("confidence_score"), [1.0])
        self.assertEqual(ctx.dumps()["measures"][0].get("confidence_score"), [1.0])

        ctx2 = ctx.copy()
        self.assertEqual(ctx2.dumps(), ctx.dumps())
