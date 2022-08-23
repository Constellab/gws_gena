
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_biota import Compound as BiotaCompound
from gws_core import (ConfigParams, Experiment, ExperimentService, File, GTest,
                      Settings, TaskRunner)
from gws_gena import (Compound, Context, ContextBuilder, ContextImporter,
                      FluxTable, FluxTableImporter, Network, NetworkImporter,
                      Reaction, Twin)

settings = Settings.retrieve()


class TestContext(BaseTestCaseUsingFullBiotaDB):

    async def test_context_builder(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")

        # flux
        file_path = os.path.join(data_dir, "ctx_data", "toy_ctx_data_1.csv")
        flux_data = FluxTableImporter.call(File(path=file_path), params=ConfigParams({"delimiter": ","}))

        # network
        file_path = os.path.join(data_dir, "toy.json")
        net = NetworkImporter.call(File(path=file_path), params=ConfigParams())

        # experiment
        tester = TaskRunner(
            inputs={"network": net, "flux_table": flux_data},
            task_type=ContextBuilder
        )

        outputs = await tester.run()

        # test results
        ctx = outputs["context"]
        expected_context = {
            "name": "context",
            "measures": [
                {
                    "id": "measure_R1_ex",
                    "name": "",
                    "lower_bound": 0.0,
                    "upper_bound": 40.0,
                    "target": 30.0,
                    "confidence_score": 1.0,
                    "variables": [
                        {
                            "reference_id": "R1_ex",
                            "reference_type": "reaction",
                            "coefficient": 1.0
                        }
                    ],
                }
            ]
        }
        print(ctx.dumps())
        self.assertEqual(ctx.dumps(), expected_context)
