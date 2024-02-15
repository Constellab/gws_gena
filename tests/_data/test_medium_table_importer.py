
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings, TaskRunner
from gws_gena import MediumTableImporter


class TestMediumTableImporter(BaseTestCaseUsingFullBiotaDB):

    def test_medium_table_importer(self):
        settings = Settings.get_instance()
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        # run trainer
        tester = TaskRunner(
            params={
                "entity_column": "Name of the metabolite",
                "chebi_column": "Chebi ID"
            },
            inputs={"source": File(path=os.path.join(data_dir, "./transporter_adder/recon_medium.csv"))},
            task_type=MediumTableImporter
        )

        outputs = tester.run()
        medium_table = outputs['target']

        self.assertEqual(medium_table.get_data().iloc[0, 0], '2-oxoglutarate')
        self.assertEqual(medium_table.get_data().iloc[0,1], '16810')
        self.assertEqual(medium_table.get_data().iloc[1, 1],'CHEBI:29985')
