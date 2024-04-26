import os
from gws_core import File, Settings, TaskRunner, BaseTestCaseLight, TableImporter
from gws_gena import TransformerEntityIDTable

class TestTransformerEntityIDTable(BaseTestCaseLight):

    def test_transformer_phenotype_table_(self):
        settings = Settings.get_instance()
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        self.print("Test TransformerPhenotypeTable")
        entity_id_table = TableImporter.call(File(path=os.path.join(data_dir, "reaction_adder/rhea_id_table.csv")), params={"index_column": -1})

        # run trainer
        runner_transformer = TaskRunner(
            inputs={"table": entity_id_table},
            task_type=TransformerEntityIDTable,
            params = {'id_column_name': "rhea_id"})

        outputs = runner_transformer.run()
        entity_id_table = outputs['transformed_table']

        self.assertEqual(entity_id_table.get_column_names(), ['entity_id'])
