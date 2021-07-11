
import os, json
import unittest
import asyncio

from gws.settings import Settings
from gws.unittest import GTest
from gws.file import File

settings = Settings.retrieve()

from gena.network import *
from gena.context import Context
from gena.recon import DraftRecon
from gena.gap_fill import GapFiller 
from gena.merge import NetworkMerger
from gena.data import *
from gena.recon_proto import ReconProto

from biota.base import DbManager as BiotaDbManager

class TestRecon(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()
        BiotaDbManager.use_prod_db(True)

    @classmethod
    def tearDownClass(cls):
        BiotaDbManager.use_prod_db(False)
        GTest.drop_tables()
        
    def test_recon_proto(self):
        GTest.print("Test ReconProto")

        data_dir = settings.get_dir("gena:testdata_dir")
        
        file_path = os.path.join(data_dir, "recon_ec_data.csv")
        ec_file = File(path=file_path)
        #ec_file.move_to_store()

        file_path = os.path.join(data_dir, "recon_medium.csv")
        medium_file = File(path=file_path)
        #medium_file.move_to_store()

        file_path = os.path.join(data_dir, "recon_biomass.csv")
        biomass_file = File(path=file_path)
        #biomass_file.move_to_store()
    
        proto = ReconProto()
        proto.input["ec_file"] = ec_file
        proto.input["biomass_file"] = biomass_file
        proto.input["medium_file"] = medium_file

        recon = proto.get_draft_recon()
        recon.set_param('tax_id', "263815")  #target pneumocyctis

        gapfiller = proto.get_gapfiller()
        gapfiller.set_param('tax_id', "4753")    #fungi 
        #gapfiller.set_param('tax_id', "2759")    #eukaryota
        gapfiller.set_param('biomass_and_medium_gaps_only', True)

        def _export_network(net, file_name):
            file_path = os.path.join(data_dir, file_name+"_net.csv")

            #with open(file_path, 'w') as f:
            #    f.write(net.to_csv())

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

        def _on_end(*args, **kwargs):
            recon_net = proto.output["draft_recon_network"]
            file_name = "recon"
            _export_network(recon_net, file_name)

            gapfill_net = proto.output["gapfiller_network"]
            file_name = "gapfill"
            _export_network(gapfill_net, file_name)

        e = proto.create_experiment(user=GTest.user, study=GTest.study)
        e.on_end( _on_end )
        asyncio.run( e.run() )
        