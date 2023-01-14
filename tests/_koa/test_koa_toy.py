import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import (ConfigParams, File, IExperiment, Settings, TaskRunner,
                      ViewTester)
from gws_gena import (KOA, Context, ContextImporter, EntityIDTable,
                      EntityIDTableImporter, KOAProto, Network,
                      NetworkImporter, Twin)

settings = Settings.get_instance()


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
                "fluxes_to_maximize": ["toy_cell_RB"],
                "relax_qssa": False,
                "ko_delimiter": ","
            },
            task_type=KOA
        )

        outputs = await tester.run()
        ko_result = outputs["koa_result"]

        print(ko_result.get_flux_dataframe("toy_cell_R1"))

        # KO: toy_cell_R1
        table = ko_result.get_flux_dataframe("toy_cell_R1")
        self.assertAlmostEqual(table.at["toy_cell_RB", "value"], 5.0, delta=1e-2)

        # KO: toy_cell_R2
        table = ko_result.get_flux_dataframe("toy_cell_R2")
        self.assertAlmostEqual(table.at["toy_cell_RB", "value"], 5.0, delta=1e-2)

        # KO: toy_cell_RB
        table = ko_result.get_flux_dataframe("toy_cell_RB")
        self.assertAlmostEqual(table.at["toy_cell_RB", "value"], 1e-9, delta=1e-2)

        # KO: toy_cell_R1,toy_cell_R2
        table = ko_result.get_flux_dataframe("toy_cell_R1,toy_cell_R2")
        self.assertAlmostEqual(table.at["toy_cell_RB", "value"], 1e-9, delta=1e-2)

        # export annotated network
        result_dir = os.path.join(data_dir, "koa")
        annotated_twin = outputs["twin"]
        net = list(annotated_twin.networks.values())[0]
        with open(os.path.join(result_dir, './toy_koa_dump.json'), 'w', encoding="utf-8") as fp:
            data = net.dumps()
            json.dump(data, fp, indent=4)

        # ko_result.view_ko_as_bar_plot(ConfigParams({
        #     "flux_names": ["toy_cell_RB","toy_cell_R2"]
        # }))
