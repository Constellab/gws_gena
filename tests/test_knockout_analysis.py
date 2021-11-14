import json
import os

import numpy
import pandas
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, Settings, TaskTester
from gws_gena import IDTable, KnockOutAnalysis, Network, TwinContext, Twin

settings = Settings.retrieve()


class TestFba(BaseTestCaseUsingFullBiotaDB):

    async def test_toy_fba(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "ko_analysis")
        net = Network.import_from_path(
            file=File(path=os.path.join(data_dir, "toy_cross_talk.json")),
            params=ConfigParams()
        )
        ctx = TwinContext.import_from_path(
            file=File(path=os.path.join(data_dir, "toy_context.json")),
            params=ConfigParams()
        )
        ko_table = IDTable.import_from_path(
            file=File(path=os.path.join(data_dir, "ko_table.csv")),
            params=ConfigParams()
        )

        twin = Twin()
        twin.add_network(network=net, related_context=ctx)
        
        tester = TaskTester(
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
