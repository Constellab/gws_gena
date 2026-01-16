import os

from gws_core import BaseTestCaseLight, File, TableImporter, TaskRunner
from gws_gena import DataProvider, TransformerPhenotypeTable


class TestTransformerPhenotypeTable(BaseTestCaseLight):
    def test_transformer_phenotype_table_(self):
        data_dir = DataProvider.get_test_data_dir()

        self.print("Test TransformerPhenotypeTable")
        phenotype_table = TableImporter.call(
            File(path=os.path.join(data_dir, "data/phenotype_table_transformer_bad_names.csv")),
            params={"index_column": -1},
        )

        # run trainer
        tester = TaskRunner(
            inputs={"table": phenotype_table},
            task_type=TransformerPhenotypeTable,
            params={
                "entity_id_column": "id_name",
                "target_column": "target_name",
                "lower_bound_column": "lower_bound_name",
                "upper_bound_column": "upper_bound_name",
                "confidence_score_column": "confidence_score_name",
            },
        )

        outputs = tester.run()
        phenotype_table = outputs["transformed_table"]

        self.assertEqual(
            phenotype_table.get_column_names(),
            ["id", "target", "lower_bound", "upper_bound", "confidence_score", "chebi_id"],
        )
