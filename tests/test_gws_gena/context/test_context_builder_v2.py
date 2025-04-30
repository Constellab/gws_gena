
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings, TaskRunner, TableImporter
from gws_gena import TransformerFluxTable
from gws_gena.network.network_task.network_importer_v2 import NetworkImporterV2
from gws_gena.context.context_builder_v2 import ContextBuilderV2

settings = Settings.get_instance()


class TestContext(BaseTestCaseUsingFullBiotaDB):

    def test_context_builder(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")

        # flux
        file_path = os.path.join(data_dir, "ctx_data", "toy_ctx_data_1.csv")
        flux_data = TableImporter.call(File(path=file_path), params={"delimiter": ","})
        transformer = TaskRunner(
            inputs={"table": flux_data},
            task_type=TransformerFluxTable,
            params = {'entity_id_column': "reaction_id",
                    'target_column': "target",
                    'lower_bound_column': "lower_bound",
                    'upper_bound_column': "upper_bound",
                    'confidence_score_column' : "confidence_score"})
        flux_data = transformer.run()['transformed_table']


        # pheno_table
        file_path = os.path.join(data_dir, "phenotype_table_context.csv")
        pheno_table = TableImporter.call(File(path=file_path), params={"delimiter": ","})

        # network
        file_path = os.path.join(data_dir, "toy.json")
        net = NetworkImporterV2.call(File(path=file_path))

        # experiment
        tester = TaskRunner(
            inputs={"network": net, "flux_table": flux_data, 'pheno_table': pheno_table},
            task_type=ContextBuilderV2
        )

        outputs = tester.run()

        # test results
        ctx = outputs["context"]
        expected_context = {
            "name": "context",
            "reaction_data": [
                {
                    "id": "rxn_R1_ex",
                    "name": "",
                    "lower_bound": [0.0],
                    "upper_bound": [40.0],
                    "target": [30.0],
                    "confidence_score": [1.0],
                    "variables": [
                        {
                            "reference_id": "R1_ex",
                            "coefficient": 1.0
                        }
                    ],
                }
            ],
            "compound_data": [
                {
                    "id": "met_X1_c",
                    "name": "",
                    "lower_bound": [0.0],
                    "upper_bound": [1000.0],
                    "target": [0.0],
                    "confidence_score": [0.0],
                    "variables": [
                        {
                            "reference_id": "X1_c",
                            "coefficient": 1.0
                        }
                    ],
                },
                {
                    "id": "met_X2_c",
                    "name": "",
                    "lower_bound": [-1],
                    "upper_bound": [10.0],
                    "target": [1.3],
                    "confidence_score": [1.0],
                    "variables": [
                        {
                            "reference_id": "X2_c",
                            "coefficient": 1.0
                        }
                    ],
                }

            ]
        }
        self.assertEqual(ctx.dumps(), expected_context)
