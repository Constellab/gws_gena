
import os

from gws_core import File, Settings, TaskRunner, BaseTestCaseLight
from gws_gena import PhenotypeTableImporter


class TestPhenotypeTableImporter(BaseTestCaseLight):

    def test_phenotype_table_importer(self):
        settings = Settings.get_instance()
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        self.print("Test PhenotypeTableImporter")

        # run trainer
        tester = TaskRunner(
            inputs={"source": File(path=os.path.join(data_dir, "data/phenotype_table_importer.csv"))},
            task_type=PhenotypeTableImporter
        )


        outputs = tester.run()
        phenotype_table = outputs['target']

        self.assertEqual(phenotype_table.get_data().iloc[0, 0], "fdp_i")
