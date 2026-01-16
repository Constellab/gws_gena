import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, TableImporter, TaskRunner
from gws_gena import (
    KOA,
    ContextImporter,
    DataProvider,
    KOAResultExtractor,
    NetworkImporter,
    TransformerEntityIDTable,
    Twin,
)


class TestKOA(BaseTestCaseUsingFullBiotaDB):
    def test_toy_koa(self):
        data_dir = DataProvider.get_test_data_dir()
        net = NetworkImporter.call(
            File(path=os.path.join(data_dir, "koa", "toy", "toy_ko.json")),
            params={"add_biomass": True},
        )
        ctx = ContextImporter.call(
            File(path=os.path.join(data_dir, "koa", "toy", "toy_ko_context.json")), {}
        )

        ko_table = TableImporter.call(
            File(path=os.path.join(data_dir, "koa", "toy", "ko_table.csv")), {}
        )
        runner_transformer = TaskRunner(
            inputs={"table": ko_table},
            task_type=TransformerEntityIDTable,
            params={"id_column_name": "id"},
        )
        ko_table = runner_transformer.run()["transformed_table"]

        twin = Twin()
        twin.add_network(network=net, related_context=ctx)

        tester = TaskRunner(
            inputs={"twin": twin, "ko_table": ko_table},
            params={
                "fluxes_to_maximize": ["toy_cell_RB"],
                "relax_qssa": False,
                "ko_delimiter": ",",
            },
            task_type=KOA,
        )

        outputs = tester.run()
        ko_result = outputs["koa_result"]

        # KO: toy_cell_R1
        table = ko_result.get_flux_dataframe("toy_cell_R1")
        self.print(table)
        self.assertAlmostEqual(table.at["toy_cell_RB", "value"], -4.304792760918324e-08, delta=1e-2)

        # KO: toy_cell_R2
        table = ko_result.get_flux_dataframe("toy_cell_R2")
        self.assertAlmostEqual(table.at["toy_cell_RB", "value"], -5.052854060470637e-08, delta=1e-2)

        # KO: toy_cell_RB
        table = ko_result.get_flux_dataframe("toy_cell_RB")
        self.print(table)
        self.assertAlmostEqual(table.at["toy_cell_RB", "value"], 9.013964577066061e-07, delta=1e-2)

        # KO: toy_cell_R1,toy_cell_R2
        table = ko_result.get_flux_dataframe("toy_cell_R1,toy_cell_R2")
        self.assertAlmostEqual(table.at["toy_cell_RB", "value"], -5.116227004950293e-08, delta=1e-2)

        # export annotated network
        result_dir = os.path.join(data_dir, "koa")
        annotated_twin = outputs["twin"]
        net = list(annotated_twin.networks.values())[0]
        with open(os.path.join(result_dir, "./toy_koa_dump.json"), "w", encoding="utf-8") as fp:
            data = net.dumps()
            json.dump(data, fp, indent=4)

        # extractor

        tester = TaskRunner(
            inputs={
                "koa_result": ko_result,
            },
            params={
                "fluxes_to_extract": ["toy_cell_RB", "toy_cell_R1"],
            },
            task_type=KOAResultExtractor,
        )
        outputs = tester.run()
        table = outputs["table"]
        self.print(table)

        data = table.get_data()
        self.assertEqual(data.shape, (8, 5))
        self.assertEqual(data.at["0", "ko_id"], "toy_cell_R1")
        self.assertEqual(data.at["0", "reaction_id"], "toy_cell_RB")
        self.assertAlmostEqual(data.at["0", "value"], -4.304792760918324e-08, delta=1e-2)
        self.assertAlmostEqual(data.at["2", "value"], 1e-9, delta=1e-2)
