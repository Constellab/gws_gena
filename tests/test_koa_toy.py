import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import (ConfigParams, File, IExperiment, Settings, TaskRunner,
                      ViewTester)
from gws_gena import (KOA, Context, ContextImporter, EntityIDTable,
                      EntityIDTableImporter, KOAProto, Network,
                      NetworkImporter, Twin)

settings = Settings.retrieve()


class TestKOA(BaseTestCaseUsingFullBiotaDB):

    async def test_toy_koa(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        net = NetworkImporter.call(
            File(path=os.path.join(data_dir, "koa", "toy", "toy_ko.json")),
            {}
        )
        ctx = ContextImporter.call(
            File(path=os.path.join(data_dir, "koa", "toy", "toy_ko_context.json")),
            {}
        )
        ko_table = EntityIDTableImporter.call(
            File(path=os.path.join(data_dir, "koa", "toy", "ko_table.csv")),
            {}
        )

        twin = Twin()
        twin.add_network(network=net, related_context=ctx)

        tester = TaskRunner(
            inputs={
                'twin': twin,
                'ko_table': ko_table
            },
            params={
                "monitored_fluxes": [],  # ["toy_cell_RB"],
                "fluxes_to_maximize": ["toy_cell_RB"],
                "relax_qssa": False,
                "ko_delimiter": ","
            },
            task_type=KOA
        )

        outputs = await tester.run()
        ko_results = outputs["result"]

        print(ko_results.get_flux_dataframe())

        self.assertEqual(ko_results.get_flux_dataframe().at[2, "ko_id"], "toy_cell_R1")
        self.assertEqual(ko_results.get_flux_dataframe().at[2, "flux_name"], "toy_cell_RB")
        self.assertAlmostEqual(ko_results.get_flux_dataframe().at[2, "flux_value"], 5.0, delta=1e-2)

        self.assertEqual(ko_results.get_flux_dataframe().at[11, "ko_id"], "toy_cell_R2")
        self.assertEqual(ko_results.get_flux_dataframe().at[11, "flux_name"], "toy_cell_RB")
        self.assertAlmostEqual(ko_results.get_flux_dataframe().at[11, "flux_value"], 5.0, delta=1e-2)

        self.assertEqual(ko_results.get_flux_dataframe().at[20, "ko_id"], "toy_cell_RB")
        self.assertEqual(ko_results.get_flux_dataframe().at[20, "flux_name"], "toy_cell_RB")
        self.assertAlmostEqual(ko_results.get_flux_dataframe().at[20, "flux_value"], 1e-9, delta=1e-2)

        self.assertEqual(ko_results.get_flux_dataframe().at[29, "ko_id"], "toy_cell_R1,toy_cell_R2")
        self.assertEqual(ko_results.get_flux_dataframe().at[29, "flux_name"], "toy_cell_RB")
        self.assertAlmostEqual(ko_results.get_flux_dataframe().at[29, "flux_value"], 1e-9, delta=1e-2)
