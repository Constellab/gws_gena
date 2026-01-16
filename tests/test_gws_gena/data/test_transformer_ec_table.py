import os

from gws_core import BaseTestCaseLight, File, TableImporter, TaskRunner
from gws_gena import DataProvider, TransformerECNumberTable


class TestTransformerECNumberTable(BaseTestCaseLight):
    def test_transformer_ec_number_table_(self):
        data_dir = DataProvider.get_test_data_dir()

        self.print("Test TransformerECNumberTable")
        ec_table = TableImporter.call(
            File(path=os.path.join(data_dir, "./data/ECnumber.csv")), params={"index_column": -1}
        )

        # run trainer
        runner_transformer = TaskRunner(
            inputs={"table": ec_table},
            task_type=TransformerECNumberTable,
            params={"ec_number_column": "ECnumber"},
        )

        outputs = runner_transformer.run()
        ec_table = outputs["transformed_table"]

        self.assertEqual(ec_table.get_column_names(), ["ec_number"])
