
import os

from gws_core import BaseTestCaseLight, File, Settings, TableImporter, TaskRunner
from gws_gena import TransformerBiomassReactionTable


class TestTransformerBiomassReactionTable(BaseTestCaseLight):

    def test_transformer_biomass_reaction_table_(self):
        settings = Settings.get_instance()
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        self.print("Test TransformerBiomassReactionTable")
        biomass_reaction_table = TableImporter.call(File(path=os.path.join(data_dir, "./recon/recon_biomass.csv")), params={"index_column": -1})

        # run trainer
        tester = TaskRunner(
            inputs={"table": biomass_reaction_table},
            task_type=TransformerBiomassReactionTable,
            params = {"entity_column": "Component",
                    "chebi_id_column": "Chebi ID",
                    "biomass_column": "Biomass"})


        outputs = tester.run()
        biomass_reaction_table = outputs['transformed_table']

        self.assertEqual(biomass_reaction_table.get_column_names(), ["entity","chebi_id","biomass", 'Protein', 'DNA', 'RNA'])
