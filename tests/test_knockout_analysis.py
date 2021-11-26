import json
import os

import numpy
import pandas
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, Settings, TaskRunner, ViewTester
from gws_gena import IDTable, KnockOutAnalysis, Network, Twin, TwinContext

settings = Settings.retrieve()


class TestFba(BaseTestCaseUsingFullBiotaDB):

    async def test_toy_fba(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        net = Network.import_from_path(
            file=File(path=os.path.join(data_dir, "ko_analysis", "toy_ko.json")),
            params=ConfigParams()
        )
        ctx = TwinContext.import_from_path(
            file=File(path=os.path.join(data_dir, "ko_analysis", "toy_ko_context.json")),
            params=ConfigParams()
        )

        ko_table = IDTable.import_from_path(
            file=File(path=os.path.join(data_dir, "ko_analysis", "ko_table.csv")),
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
                "monitored_fluxes": ["toy_cell_RB"],
                "fluxes_to_maximize": ["toy_cell_RB"],
                "relax_qssa": True
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
            view=ko_results.view_as_bar_plot(params)
        )

        view_dict = tester.to_dict()
        print(view_dict)

        self.assertEqual(view_dict["data"]["nb_of_columns"], 2)
        self.assertEqual(len(view_dict["data"]["views"]), 2)
