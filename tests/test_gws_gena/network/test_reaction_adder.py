import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings, TableImporter, TaskRunner
from gws_gena import DataProvider, NetworkImporter, ReactionAdder, TransformerEntityIDTable

settings = Settings.get_instance()


class TestReactionAdder(BaseTestCaseUsingFullBiotaDB):
    def test_reaction_ec_adder(self):
        self.print("Test reaction EC adder")
        data_dir = DataProvider.get_test_data_dir()
        net = NetworkImporter.call(
            File(path=os.path.join(data_dir, "toy", "toy.json")), params={"add_biomass": True}
        )
        table = TableImporter.call(
            File(path=os.path.join(data_dir, "reaction_adder", "ec_table.csv")), params={}
        )

        tester = TaskRunner(
            params={"tax_id": "2759"},
            inputs={"network": net, "reaction_table": table},
            task_type=ReactionAdder,
        )
        outputs = tester.run()
        net = outputs["network"]
        # print(net.to_csv())
        self.assertEqual(len(net.reactions), 9)
        self.assertTrue("RHEA:15133" in str(net.reactions))
        self.assertTrue("RHEA:16169" in str(net.reactions))

        # file_path = os.path.join(data_dir, "reaction_adder", "toy_with_added_ec.json")
        # with open(file_path, 'w') as f:
        #     json.dump(net.dumps(), f)

    def test_reaction_id_adder(self):
        self.print("Test reaction ID adder")
        data_dir = DataProvider.get_test_data_dir()
        net = NetworkImporter.call(
            File(path=os.path.join(data_dir, "toy", "toy.json")), params={"add_biomass": True}
        )
        self.assertEqual(len(net.reactions), 7)

        table = TableImporter.call(
            File(path=os.path.join(data_dir, "reaction_adder", "rhea_id_table.csv")), {}
        )
        runner_transformer = TaskRunner(
            inputs={"table": table},
            task_type=TransformerEntityIDTable,
            params={"id_column_name": "rhea_id"},
        )
        table = runner_transformer.run()["transformed_table"]

        tester = TaskRunner(
            params={}, inputs={"network": net, "reaction_table": table}, task_type=ReactionAdder
        )
        outputs = tester.run()
        net = outputs["network"]

        self.assertEqual(len(net.reactions), 8)

        self.print(str(net.reactions))
        self.assertTrue("RHEA:16505" in str(net.reactions))

        # file_path = os.path.join(data_dir, "reaction_adder", "toy_with_added_id.json")
        # with open(file_path, 'w') as f:
        #     json.dump(net.dumps(), f)
