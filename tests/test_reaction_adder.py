
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, Settings, TaskRunner
from gws_gena import ECTable, IDTable, Network, ReactionAdder

settings = Settings.retrieve()


class TestReactionAdder(BaseTestCaseUsingFullBiotaDB):

    async def test_reaction_ec_adder(self):
        self.print("Test reaction EC adder")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        net = Network.import_from_path(File(path=os.path.join(data_dir, "toy", "toy.json")), params=ConfigParams())
        table = ECTable.import_from_path(
            File(path=os.path.join(data_dir, "reaction_adder", "ec_table.csv")),
            params=ConfigParams())

        tester = TaskRunner(
            params={"tax_id": "2759"},
            inputs={"network": net, "reaction_table": table},
            task_type=ReactionAdder
        )
        outputs = await tester.run()
        net = outputs["network"]
        # print(net.to_csv())
        self.assertEqual(len(net.reactions), 9)
        self.assertTrue("RHEA_15133_1_4_1_2" in net.reactions)
        self.assertTrue("RHEA_16169_6_3_1_2" in net.reactions)

        # file_path = os.path.join(data_dir, "reaction_adder", "toy_with_added_ec.json")
        # with open(file_path, 'w') as f:
        #     json.dump(net.dumps(), f)

    async def test_reaction_id_adder(self):
        self.print("Test reaction ID adder")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        net = Network.import_from_path(File(path=os.path.join(data_dir, "toy", "toy.json")), params=ConfigParams())
        table = IDTable.import_from_path(
            File(path=os.path.join(data_dir, "reaction_adder", "rhea_id_table.csv")),
            params=ConfigParams({'id_column': 'rhea_id'}))

        tester = TaskRunner(
            params={},
            inputs={"network": net, "reaction_table": table},
            task_type=ReactionAdder
        )
        outputs = await tester.run()
        net = outputs["network"]

        # print(net.to_csv())
        self.assertEqual(len(net.reactions), 8)
        self.assertTrue("RHEA_16505_4_1_3_40" in net.reactions)

        # file_path = os.path.join(data_dir, "reaction_adder", "toy_with_added_id.json")
        # with open(file_path, 'w') as f:
        #     json.dump(net.dumps(), f)
