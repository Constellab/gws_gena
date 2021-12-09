import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, Settings, TaskRunner, ViewTester
from gws_gena import IDTable, KnockOutAnalysis, Network, Twin, TwinContext

settings = Settings.retrieve()


class TestFba(BaseTestCaseUsingFullBiotaDB):

    async def test_toy_koa(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        net = Network.import_from_path(
            file=File(path=os.path.join(data_dir, "ko_analysis", "toy", "toy_ko.json")),
            params=ConfigParams()
        )
        ctx = TwinContext.import_from_path(
            file=File(path=os.path.join(data_dir, "ko_analysis", "toy", "toy_ko_context.json")),
            params=ConfigParams()
        )

        ko_table = IDTable.import_from_path(
            file=File(path=os.path.join(data_dir, "ko_analysis", "toy", "ko_table.csv")),
            params=ConfigParams()
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
                "relax_qssa": True,
                "ko_delimiter": ","
            },
            task_type=KnockOutAnalysis
        )

        outputs = await tester.run()
        ko_results = outputs["ko_analysis_result"]

        print(ko_results)

        params = ConfigParams({
            "flux_names": ["toy_cell_RB", "toy_cell_R1"]
        })
        tester = ViewTester(
            view=ko_results.view_ko_summary_as_bar_plot(params)
        )

        view_dict = tester.to_dict()
        print(view_dict)

        self.assertEqual(view_dict["data"]["nb_of_columns"], 2)
        self.assertEqual(len(view_dict["data"]["views"]), 2)

        self.assertEqual(ko_results.get_data().at[0, "ko_id"], "toy_cell_R1")
        self.assertEqual(ko_results.get_data().at[0, "flux_name"], "toy_cell_R1")
        self.assertAlmostEqual(ko_results.get_data().at[0, "flux_value"], 0.000193, delta=1e-6)

    async def test_ecoli_koa(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        net = Network.import_from_path(
            file=File(path=os.path.join(data_dir, "ecoli", "ecoli.json")),
            params=ConfigParams()
        )
        ctx = TwinContext.import_from_path(
            file=File(path=os.path.join(data_dir, "ecoli", "ecoli_context.json")),
            params=ConfigParams()
        )

        ko_table = IDTable.import_from_path(
            file=File(path=os.path.join(data_dir, "ko_analysis", "ecoli", "ko_table.csv")),
            params=ConfigParams()
        )

        twin = Twin()
        twin.add_network(network=net, related_context=ctx)
        tester = TaskRunner(
            inputs={
                'twin': twin,
                'ko_table': ko_table
            },
            params={
                "monitored_fluxes": ["ecoli_BIOMASS_Ecoli_core_w_GAM"],
                "fluxes_to_maximize": ["ecoli_BIOMASS_Ecoli_core_w_GAM"],
                "solver": "quad",
                "relax_qssa": True
            },
            task_type=KnockOutAnalysis
        )

        outputs = await tester.run()
        ko_results = outputs["ko_analysis_result"]

        print(ko_results)

        # params = ConfigParams({
        #     "flux_names": ["toy_cell_RB", "toy_cell_R1"]
        # })
        # tester = ViewTester(
        #     view=ko_results.view_ko_summary_as_bar_plot(params)
        # )

        # view_dict = tester.to_dict()
        # print(view_dict)

        # self.assertEqual(view_dict["data"]["nb_of_columns"], 2)
        # self.assertEqual(len(view_dict["data"]["views"]), 2)

        # self.assertEqual(ko_results.get_data().at[0, "ko"], "toy_cell_R1")
        # self.assertEqual(ko_results.get_data().at[0, "flux_name"], "toy_cell_R1")
        # self.assertAlmostEqual(ko_results.get_data().at[0, "flux_value"], 0.000193, delta=1e-6)
