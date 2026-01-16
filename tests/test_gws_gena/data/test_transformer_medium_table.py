import os

from gws_core import BaseTestCaseLight, File, TableImporter, TaskRunner
from gws_gena import DataProvider, TransformerMediumTable


class TestTransformerMediumTable(BaseTestCaseLight):
    def test_transformer_medium_table_(self):
        data_dir = DataProvider.get_test_data_dir()

        self.print("Test TransformerMediumTable")
        biomass_reaction_table = TableImporter.call(
            File(path=os.path.join(data_dir, "./transporter_adder/recon_medium.csv")),
            params={"index_column": -1},
        )

        # run trainer
        tester = TaskRunner(
            inputs={"table": biomass_reaction_table},
            task_type=TransformerMediumTable,
            params={"entity_column": "Name of the metabolite", "chebi_id_column": "Chebi ID"},
        )

        outputs = tester.run()
        biomass_reaction_table = outputs["transformed_table"]

        self.assertEqual(biomass_reaction_table.get_column_names(), ["entity", "chebi_id"])
