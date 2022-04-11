import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import (ConfigParams, Experiment, File, IExperiment, Settings,
                      TaskRunner)
from gws_gena import (BiomassReactionTableImporter, DraftRecon,
                      ECTableImporter, GapFiller, MediumTableImporter,
                      NetworkMerger, ReconProto, Context)

settings = Settings.retrieve()


class TestRecon(BaseTestCaseUsingFullBiotaDB):

    async def test_recon_proto(self):
        self.print("Test ReconProto")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "recon")

        ec_table = ECTableImporter.call(File(
            path=os.path.join(data_dir, "recon_ec_table.csv")),
            {
                "ec_column": "EC Number"
        }
        )

        biomass_table = BiomassReactionTableImporter.call(File(
            path=os.path.join(data_dir, "recon_biomass.csv")),
            {
                "entity_column": "Component",
                "chebi_column": "Chebi ID",
                "biomass_column": "Biomass"
        }
        )

        medium_table = MediumTableImporter.call(File(
            path=os.path.join(data_dir, "recon_medium.csv")),
            {
                "entity_column": "Name of the metabolite",
                "chebi_column": "Chebi ID"
        }
        )

        experiment = IExperiment(ReconProto)
        proto = experiment.get_protocol()

        proto.set_input("ec_table", ec_table)
        proto.set_input("biomass_table", biomass_table)
        proto.set_input("medium_table", medium_table)

        recon = proto.get_process("recon")
        recon.set_param('tax_id', "263815")  # pcystis murina

        gap_filler = proto.get_process("gap_filler")
        gap_filler.set_param('tax_id', "4753")  # pcystis
        # gap_filler.set_param('tax_id', "4751")
        # #fungi
        # gap_filler.set_param('tax_id', "2759")    #eukaryota
        gap_filler.set_param('biomass_and_medium_gaps_only', True)
        gap_filler.set_param('add_sink_reactions', True)

        async def assert_results(net, file_name):
            # file_path = os.path.join(data_dir, file_name+"_net.csv")
            # with open(file_path, 'w', encoding="utf-8") as f:
            #     f.write(net.to_csv())

            # file_path = os.path.join(data_dir, file_name+"_net.json")
            # with open(file_path, 'w', encoding="utf-8") as f:
            #     json.dump(net.dumps(), f)

            file_path = os.path.join(data_dir, file_name+"_net.csv")
            with open(file_path, 'r', encoding="utf-8") as f:
                print(net.to_csv())
                self.assertEqual(net.to_csv(), f.read())

            # file_path = os.path.join(data_dir, file_name+"_stats.csv")
            # with open(file_path, 'w', encoding="utf-8") as f:
            #     table = net.get_compound_stats_as_table()
            #     f.write(table.to_csv())

            # file_path = os.path.join(data_dir, file_name+"_gaps.csv")
            # with open(file_path, 'w', encoding="utf-8") as f:
            #     table = net.get_gaps_as_table()
            #     f.write(table.to_csv())

        # run experiment
        await experiment.run()

        # test results
        recon_net = proto.get_output("draft_recon_network")
        file_name = "recon"
        await assert_results(recon_net, file_name)

        gapfill_net = proto.get_output("gap_filler_network")
        file_name = "gapfill"
        await assert_results(gapfill_net, file_name)

    # async def test_recon_using_tax_id(self):
    #     self.print("Test Recon using tax_id only")

    #     organisms = {
    #         "eukaryota": "2759",
    #         "sapiens": "9606",
    #         "yeast": "4932",
    #         "mus musculus": "10090"
    #     }

    #     name = "sapiens"
    #     tester = TaskRunner(
    #         task_type=DraftRecon,
    #         inputs={},
    #         params={"tax_id": organisms[name]}
    #     )
    #     outputs = await tester.run()
    #     net = outputs["network"]

    #     data_dir = settings.get_variable("gws_gena:testdata_dir")
    #     data_dir = os.path.join(data_dir, "recon/build", name)
    #     if not os.path.exists(data_dir):
    #         os.makedirs(data_dir)

    #     file_path = os.path.join(data_dir, f"{name}.json")
    #     with open(file_path, 'w') as f:
    #         json.dump(net.view_as_network().to_dict(ConfigParams()), f)

    #     # print(len(net.reactions))
