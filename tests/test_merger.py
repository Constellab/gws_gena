
import os, json
import unittest
import asyncio

from gws.protocol import Protocol
from gws.settings import Settings
from gws.unittest import GTest
from gws.file import File

settings = Settings.retrieve()

from gena.network import *
from gena.context import Context
from gena.biomodel import BioModel
from gena.recon import DraftRecon
from gena.gap_fill import GapFiller 
from gena.merge import NetworkMerger
from gena.data import *
from gena.recon_proto import ReconProto

from biota.base import DbManager as BiotaDbManager

class TestMerge(unittest.TestCase):
    
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

    def test_merger(self):
        GTest.print("Test Merger")
        data_dir = settings.get_dir("gena:testdata_dir")
        file_path = os.path.join(data_dir, "recon", "recon_net.json")
        net_loader_1 = NetworkLoader()
        net_loader_1.set_param("file_path", file_path)

        file_path = os.path.join(data_dir, "merge", "addon.json")
        net_loader_2 = NetworkLoader()
        net_loader_2.set_param("file_path", file_path)
        merger = NetworkMerger()
        
        proto = Protocol(
            processes = {
                "merger": merger,
                "net_loader_1": net_loader_1,
                "net_loader_2": net_loader_2
            },
            connectors = [
                net_loader_1>>"data" | merger<<"network_1",
                net_loader_2>>"data" | merger<<"network_2"
            ]
        )
        
        result_dir = os.path.join(data_dir, "merge")
        def _export_network(net, file_name):
            # file_path = os.path.join(result_dir, file_name+"_net.csv")
            # with open(file_path, 'w') as f:
            #    f.write(net.to_csv())

            # file_path = os.path.join(result_dir, file_name+"_net.json")
            # with open(file_path, 'w') as f:
            #     json.dump(net.to_json(), f)

            file_path = os.path.join(result_dir, file_name+"_net.csv")
            with open(file_path, 'r') as f:
                self.assertEqual(net.to_csv(), f.read())

            file_path = os.path.join(result_dir, file_name+"_stats.csv")
            with open(file_path, 'w') as f:
                table = net.render__compound_stats__as_table()
                f.write(table.to_csv())
            
            file_path = os.path.join(result_dir, file_name+"_gaps.csv")
            with open(file_path, 'w') as f:
                table = net.render__gaps__as_table()
                f.write(table.to_csv())
            
        def _on_end(*args, **kwargs):
            net = merger.output['network']
            file_name = "merger"
            _export_network(net, file_name)

        e = proto.create_experiment( study=GTest.study, user=GTest.user )
        e.on_end( _on_end )
        asyncio.run( e.run() )