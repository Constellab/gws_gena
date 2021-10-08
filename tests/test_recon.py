
import os, json

from gws_core import Settings, IExperiment, Experiment, File, TaskTester
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_gena import TwinContext, DraftRecon, GapFiller, NetworkMerger
from gws_gena.proto import ReconProto

settings = Settings.retrieve()

class TestRecon(BaseTestCaseUsingFullBiotaDB):
    
    async def test_recon_proto(self):
        self.print("Test ReconProto")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "recon")

        file_path = os.path.join(data_dir, "recon_ec_table.csv")
        ec_file = File()
        ec_file.path = file_path

        file_path = os.path.join(data_dir, "recon_medium.csv")
        medium_file = File()
        medium_file.path = file_path

        file_path = os.path.join(data_dir, "recon_biomass.csv")
        biomass_file = File()
        biomass_file.path = file_path

        experiment = IExperiment( ReconProto )
        proto = experiment.get_protocol()

        proto.set_input("ec_file", ec_file)
        proto.set_input("biomass_file", biomass_file)
        proto.set_input("medium_file", medium_file)

        recon = proto.get_process("recon")
        recon.set_param('tax_id', "263815")  #pcystis murina

        gap_filler = proto.get_process("gap_filler")
        gap_filler.set_param('tax_id', "4753")    #pcystis 
        #gap_filler.set_param('tax_id', "4751")    #fungi
        #gap_filler.set_param('tax_id', "2759")    #eukaryota
        gap_filler.set_param('biomass_and_medium_gaps_only', True)
        gap_filler.set_param('add_sink_reactions', True)

        async def assert_results(net, file_name):
            # file_path = os.path.join(data_dir, file_name+"_net.csv")
            # with open(file_path, 'w') as f:
            #     f.write(net.to_csv())

            # file_path = os.path.join(data_dir, file_name+"_net.json")
            # with open(file_path, 'w') as f:
            #     json.dump(net.dumps(), f)

            file_path = os.path.join(data_dir, file_name+"_net.csv")
            with open(file_path, 'r') as f:
                self.assertEqual(net.to_csv(), f.read())

            file_path = os.path.join(data_dir, file_name+"_stats.csv")
            with open(file_path, 'w') as f:
                table = net.render__compound_stats__as_table()
                f.write(table.to_csv())
            
            file_path = os.path.join(data_dir, file_name+"_gaps.csv")
            with open(file_path, 'w') as f:
                table = net.render__gaps__as_table()
                f.write(table.to_csv())

        # run experiment
        await experiment.run()

        # test results
        recon_net = proto.get_output("draft_recon_network")
        file_name = "recon"
        await assert_results(recon_net, file_name)

        gapfill_net = proto.get_output("gap_filler_network")
        file_name = "gapfill"
        await assert_results(gapfill_net, file_name)

    async def test_recon_using_tax_id(self):
        return
        self.print("Test Recon using tax_id only")

        #eukaryota => 2759
        #sapiens => 9606
        #yeast => 4932
        #mus musculus => 10090

        tester = TaskTester(
            task_type = DraftRecon,
            inputs = {},
            params = {"tax_id": "2759"} 
        )
        outputs = await tester.run()
        net = outputs["network"]

        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "eukaryota")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        file_path = os.path.join(data_dir, "net.json")
        with open(file_path, 'w') as f:
             json.dump(net.dumps(), f)

        print(len(net.reactions))

        