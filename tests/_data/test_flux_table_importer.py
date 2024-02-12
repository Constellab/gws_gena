
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings, TaskRunner
from gws_gena import FluxTableImporter


class TestFluxTableImporter(BaseTestCaseUsingFullBiotaDB):

    def test_importer(self):
        settings = Settings.get_instance()
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        self.print(f"Test Flux Table importer : only one simulation")

        # run trainer
        tester = TaskRunner(
            inputs={"source": File(path=os.path.join(data_dir, "toy/ctx_data/toy_ctx_data_1.csv"))},
            task_type=FluxTableImporter
        )

        outputs = tester.run()
        flux_table = outputs['target']

        self.assertEqual(flux_table.get_data().iloc[0, 0], "R1_ex")
        self.assertEqual(flux_table.get_data().iloc[0,1], 30.0)

        self.print(f"Test Flux Table importer : multiple simulations")

        tester = TaskRunner(
            inputs={"source": File(path=os.path.join(data_dir, "data/fluxTableMulti.csv"))},
            task_type=FluxTableImporter
        )

        outputs = tester.run()
        flux_table = outputs['target']

        self.assertEqual(flux_table.get_data().iloc[0, 0], "PFK")
        self.assertEqual(flux_table.get_data().iloc[0,1], "[4, 4.2, 4.3]")
