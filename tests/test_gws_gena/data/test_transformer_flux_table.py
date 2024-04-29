
import os
from gws_core import File, Settings, TaskRunner, BaseTestCaseLight, TableImporter
from gws_gena import TransformerFluxTable

class TestTransformerFluxTable(BaseTestCaseLight):

    def test_transformer_phenotype_table_(self):
        settings = Settings.get_instance()
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        self.print("Test TransformerFluxTable")
        self.print("Test Flux Table importer : only one simulation")

        flux_table = TableImporter.call(File(path=os.path.join(data_dir, "toy/ctx_data/toy_ctx_data_1.csv")), params={"index_column": -1})

        # run trainer
        tester = TaskRunner(
            inputs={"table": flux_table},
            task_type=TransformerFluxTable,
            params = {'entity_id_column': "reaction_id",
                    'target_column': "target",
                    'lower_bound_column': "lower_bound",
                    'upper_bound_column': "upper_bound",
                    'confidence_score_column' : "confidence_score"})

        outputs = tester.run()
        flux_table = outputs['transformed_table']


        self.assertEqual(flux_table.get_data().iloc[0, 0], "R1_ex")
        self.assertEqual(flux_table.get_data().iloc[0,1], 30.0)
        self.assertEqual(flux_table.get_column_names(), ['id', 'target', 'lower_bound', 'upper_bound', 'confidence_score'])

        self.print("Test Flux Table importer : multiple simulations")

        flux_table = TableImporter.call(File(path=os.path.join(data_dir, "data/fluxTableMulti.csv")), params={"index_column": -1})

        # run trainer
        tester = TaskRunner(
            inputs={"table": flux_table},
            task_type=TransformerFluxTable,
            params = {'entity_id_column': "reaction_id",
                    'target_column': "target",
                    'lower_bound_column': "lower_bound",
                    'upper_bound_column': "upper_bound",
                    'confidence_score_column' : "confidence_score"})

        outputs = tester.run()
        flux_table = outputs['transformed_table']

        self.assertEqual(flux_table.get_data().iloc[0, 0], "PFK")
        self.assertEqual(flux_table.get_data().iloc[0,1], "[4, 4.2, 4.3]")
        self.assertEqual(flux_table.get_column_names(), ['id', 'target', 'lower_bound', 'upper_bound', 'confidence_score'])
