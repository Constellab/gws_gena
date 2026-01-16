
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings, TableImporter, TaskRunner
from gws_gena import NetworkImporter, ReactionRemover, TransformerEntityIDTable

settings = Settings.get_instance()


class TestReactionremover(BaseTestCaseUsingFullBiotaDB):

    def test_reaction_ec_remover(self):
        self.print("Test reaction EC remover")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        net = NetworkImporter.call(
            File(
                path=os.path.join(
                    data_dir, "reaction_remover", "toy_with_added_reactions.json")),
            params={"add_biomass" : True})
        table = TableImporter.call(
            File(path=os.path.join(data_dir, "reaction_remover", "ec_table.csv")),
            params={})

        tester = TaskRunner(
            params={},
            inputs={"network": net, "reaction_table": table},
            task_type=ReactionRemover
        )
        outputs = tester.run()
        net = outputs["network"]

        original_net = NetworkImporter.call(
            File(path=os.path.join(data_dir,  "reaction_remover", "toy_with_added_reactions.json")),
            params={"add_biomass" : True}
        )

        self.assertEqual(len(net.reactions), 7)
        self.assertTrue("RHEA_15133_1_4_1_2" in original_net.reactions)
        self.assertTrue("RHEA_16169_6_3_1_2" in original_net.reactions)
        self.assertTrue("RHEA_15133_1_4_1_2" not in net.reactions)
        self.assertTrue("RHEA_16169_6_3_1_2" not in net.reactions)

    def test_reaction_id_remover(self):
        self.print("Test reaction ID remover")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        net = NetworkImporter.call(
            File(
                path=os.path.join(
                    data_dir, "reaction_remover", "toy_with_added_reactions.json")),
            params={"add_biomass" : True})

        table = TableImporter.call(
            File(path=os.path.join(data_dir, "reaction_remover", "id_table.csv")),
            {}
        )
        runner_transformer = TaskRunner( inputs={"table": table},
            task_type=TransformerEntityIDTable, params = {'id_column_name': "ids"})
        table = runner_transformer.run()['transformed_table']


        tester = TaskRunner(
            params={},
            inputs={"network": net, "reaction_table": table},
            task_type=ReactionRemover
        )
        outputs = tester.run()
        net = outputs["network"]
        print(net.to_csv())

        original_net = NetworkImporter.call(
            File(path=os.path.join(data_dir,  "reaction_remover", "toy_with_added_reactions.json")),
            params={"add_biomass" : True}
        )

        # self.assertEqual(len(net.reactions), 7)
        self.assertTrue("R5_ex" not in net.reactions)
        self.assertTrue("RHEA_16169_6_3_1_2" not in net.reactions)

        self.assertTrue("R5_ex" in original_net.reactions)
        self.assertTrue("RHEA_16169_6_3_1_2" in original_net.reactions)
