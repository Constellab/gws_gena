
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings, TaskRunner,BaseTestCaseLight
from gws_gena import EntityIDTableImporter


class TestEntityIdImporter(BaseTestCaseLight):

    def test_importer(self):
        settings = Settings.get_instance()
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        self.print(f"Test EntityIDTableImporter")

        # run trainer
        tester = TaskRunner(
            inputs={"source": File(path=os.path.join(data_dir, "reaction_adder/rhea_id_table.csv"))},
            params={'id_column': 'rhea_id'},
            task_type=EntityIDTableImporter
        )

        outputs = tester.run()
        entity_id_table = outputs['target']

        self.assertEqual(entity_id_table.get_data().iloc[0, 0], "RHEA:16505")
