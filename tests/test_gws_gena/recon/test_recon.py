import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, ScenarioProxy, TableImporter, TaskRunner
from gws_gena import (
    DataProvider,
    ReconProto,
    TransformerBiomassReactionTable,
    TransformerECNumberTable,
)


class TestRecon(BaseTestCaseUsingFullBiotaDB):
    def test_recon_proto(self):
        data_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(data_dir, "recon")

        ec_table = TableImporter.call(File(path=os.path.join(data_dir, "recon_ec_table.csv")))

        # run transformer
        runner_transformer = TaskRunner(
            inputs={"table": ec_table},
            task_type=TransformerECNumberTable,
            params={"ec_number_column": "EC Number"},
        )

        ec_table = runner_transformer.run()["transformed_table"]

        # run transformer
        biomass_table = TableImporter.call(File(path=os.path.join(data_dir, "recon_biomass.csv")))
        runner_transformer_biomasss = TaskRunner(
            inputs={"table": biomass_table},
            task_type=TransformerBiomassReactionTable,
            params={
                "entity_column": "Component",
                "chebi_id_column": "Chebi ID",
                "biomass_column": "Biomass",
            },
        )

        biomass_table = runner_transformer_biomasss.run()["transformed_table"]

        experiment = ScenarioProxy(ReconProto)
        proto = experiment.get_protocol()

        # Add ec_table as input resource
        recon_process = proto.get_process("recon")
        proto.add_resource(
            instance_name="ec_table_input",
            resource_model_id=str(ec_table.id),
            in_port=recon_process << "ec_table",
        )

        # Add biomass_table as input resource
        proto.add_resource(
            instance_name="biomass_table_input",
            resource_model_id=str(biomass_table.id),
            in_port=recon_process << "biomass_table",
        )

        recon = proto.get_process("recon")
        # recon.set_param('tax_id', "4753")  # pcystis
        recon.set_param("tax_id", "263815")  # pcystis murina

        gap_filler = proto.get_process("gap_filler")
        # gap_filler.set_param('tax_id', "4753")      # pcystis
        gap_filler.set_param("tax_id", "4751")  # fungi
        # gap_filler.set_param('tax_id', "2759")    # eukaryota
        # gap_filler.set_param('biomass_and_medium_gaps_only', True)
        # gap_filler.set_param('add_sink_reactions', True)

        # run experiment
        experiment.run()

        # test results
        recon_net = proto.get_output("draft_recon_network")

        # TESTS

        # file_name = "recon"
        # file_path = os.path.join(data_dir, "recon_latest", file_name+"_net.csv")
        # with open(file_path, 'w', encoding="utf-8") as f:
        #     f.write(recon_net.to_csv())
        # file_path = os.path.join(data_dir, "recon_latest", file_name+"_net.json")
        # with open(file_path, 'w', encoding="utf-8") as f:
        #     json.dump(recon_net.dumps(), f)

        # file_name = "recon"
        # file_path = os.path.join(data_dir, "recon_latest", file_name+"_net.csv")
        # with open(file_path, 'r', encoding="utf-8") as f:
        #     self.assertEqual(recon_net.to_csv(), f.read())

        # gapfill_net = proto.get_output("gap_filler_network")
        # file_name = "gapfill"
        # assert_results(gapfill_net, file_name)

        # file_name = "recon"
        # file_path = os.path.join(data_dir, file_name+"_net.xlsx")
        # df = recon_net.to_dataframe()
        # df.to_excel(file_path)

        # print(len(recon_net.reactions))
        # print(len(recon_net.compounds))
        self.assertEqual(len(recon_net.reactions), 37)
        self.assertEqual(len(recon_net.compounds), 100)

        comp_ids = recon_net.get_compound_ids()
        self.assertTrue("Biomass_cytosol" in comp_ids)
        self.assertTrue("CHEBI:16526_cytosol" in comp_ids)

        rxn_ids = recon_net.get_reaction_ids()
        self.assertTrue("RHEA:16585" in rxn_ids)
        self.assertTrue("RHEA:15481" in rxn_ids)
