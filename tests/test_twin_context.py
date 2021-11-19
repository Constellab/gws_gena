
import os, json

from gws_core import Settings, GTest, Experiment, ExperimentService, TaskRunner, File, ConfigParams
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_biota import Compound as BiotaCompound
from gws_gena import Network, Compound, Reaction
from gws_gena import Twin, TwinContext, TwinContextBuilder
from gws_gena import FluxTable

settings = Settings.retrieve()

class TestContext(BaseTestCaseUsingFullBiotaDB):

    def test_context(self):
        self.print("Test TwinContext")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")
        file_path = os.path.join(data_dir, "toy_context.json")
        ctx = TwinContext.import_from_path(File(path=file_path), params=ConfigParams())

        with open(file_path) as f:
            data = json.load(f)
              
        print(ctx.dumps())

        self.assertEqual( data["measures"][1], ctx.dumps()["measures"][1] )
        self.assertEqual( data["measures"][0].get("confidence_score"), 1.0 )
        self.assertEqual( ctx.dumps()["measures"][0].get("confidence_score"), 1.0 )
        
        ctx2 = ctx.copy()
        self.assertEqual( ctx2.dumps(), ctx.dumps() )
        
    async def test_context_builder(self):
        self.print("Test TwinContext Builder")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")
        
        # flux
        file_path = os.path.join(data_dir, "toy_flux_data.csv")
        flux_data = FluxTable.import_from_path(File(path=file_path), params=ConfigParams({"delimiter":","}))

        # network
        file_path = os.path.join(data_dir, "toy.json")
        net = Network.import_from_path(File(path=file_path), params=ConfigParams())

        # experiment
        tester = TaskRunner(
            inputs = {"network": net, "flux_table": flux_data},
            task_type = TwinContextBuilder
        )

        outputs = await tester.run()
  
        # test results
        ctx = outputs["context"]
        expected_context = {
            "measures": [
                {
                    "id": "measure_R1_ex",
                    "name": "",
                    "variables": [
                        {
                            "reference_id": "R1_ex",
                            "reference_type": "reaction",
                            "coefficient": 1.0
                        }
                    ],
                    "lower_bound": 0.0,
                    "upper_bound": 40.0,
                    "target": 30.0,
                    "confidence_score": 1.0
                }
            ]
        }

        print(ctx.dumps())

        self.assertEqual(ctx.dumps(), expected_context)