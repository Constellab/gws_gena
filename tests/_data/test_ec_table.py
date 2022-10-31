
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings, TaskRunner
from gws_gena import ECTableImporter


class TestECTableImporter(BaseTestCaseUsingFullBiotaDB):

    async def test_importer(self):
        settings = Settings.retrieve()
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        # run trainer
        tester = TaskRunner(
            params={"ec_column": "ECnumber"},
            inputs={"source": File(path=os.path.join(data_dir, "./data/ECnumber.csv"))},
            task_type=ECTableImporter
        )
        outputs = await tester.run()
        ds = outputs['target']

        self.assertEqual(ds.get_data().iloc[0, 0], "4.1.1.28")
        self.assertEqual(ds.get_data().iloc[2, 0], "1.14.17.1")
        print(ds)