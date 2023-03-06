import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, IExperiment, Settings
from gws_gena import (BiomassReactionTableImporter, ECTableImporter,
                      MediumTableImporter, ReconProto)

settings = Settings.get_instance()


class TestRecon(BaseTestCaseUsingFullBiotaDB):

    def test_recon_proto(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "recon")

        ec_table = ECTableImporter.call(File(
            path=os.path.join(data_dir, "recon_ec_table.csv")),
            {
                "ec_column": "EC Number"
        })

        biomass_table = BiomassReactionTableImporter.call(File(
            path=os.path.join(data_dir, "recon_biomass.csv")),
            {
                "entity_column": "Component",
                "chebi_column": "Chebi ID",
                "biomass_column": "Biomass"
        })

        medium_table = MediumTableImporter.call(File(
            path=os.path.join(data_dir, "recon_medium.csv")),
            {
                "entity_column": "Name of the metabolite",
                "chebi_column": "Chebi ID"
        })

        experiment = IExperiment(ReconProto)
        proto = experiment.get_protocol()

        proto.set_input("ec_table", ec_table)
        proto.set_input("biomass_table", biomass_table)
        proto.set_input("medium_table", medium_table)

        recon = proto.get_process("recon")
        # recon.set_param('tax_id', "4753")  # pcystis
        recon.set_param('tax_id', "263815")  # pcystis murina

        gap_filler = proto.get_process("gap_filler")
        gap_filler.set_param('tax_id', "4753")      # pcystis
        # gap_filler.set_param('tax_id', "4751")    # fungi
        # gap_filler.set_param('tax_id', "2759")    # eukaryota
        # gap_filler.set_param('biomass_and_medium_gaps_only', True)
        # gap_filler.set_param('add_sink_reactions', True)

        def assert_results(net, file_name):
            # file_path = os.path.join(data_dir, file_name+"_net.csv")
            # with open(file_path, 'w', encoding="utf-8") as f:
            #     f.write(net.to_csv())
            # file_path = os.path.join(data_dir, file_name+"_net.json")
            # with open(file_path, 'w', encoding="utf-8") as f:
            #     json.dump(net.dumps(), f)

            file_path = os.path.join(data_dir, file_name+"_net.csv")
            with open(file_path, 'r', encoding="utf-8") as f:
                self.assertEqual(net.to_csv(), f.read())

        # run experiment
        experiment.run()

        # test results
        recon_net = proto.get_output("draft_recon_network")
        file_name = "recon"
        assert_results(recon_net, file_name)

        # gapfill_net = proto.get_output("gap_filler_network")
        # file_name = "gapfill"
        # await assert_results(gapfill_net, file_name)
