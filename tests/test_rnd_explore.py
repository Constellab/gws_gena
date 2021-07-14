
import asyncio
import os, json
import unittest

from gws.settings import Settings
from gws.unittest import GTest
from gws.file import File
settings = Settings.retrieve()

from gena.network import Network
from gena.context import Context
from gena.biomodel import BioModel
from gena.rnd_explore import RndExplorer, RndExplorerResult
from gena.rnd_explore_proto import RndExplorerProto

from biota.base import DbManager as BiotaDbManager

class TestRndExplorer(unittest.TestCase):
    
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

    def test_rnd_exploreer_proto(self):
        GTest.print("Test RndExplorerProto")
        organism = "ecoli"
        data_dir = settings.get_dir("gena:testdata_dir")
        organism_dir = os.path.join(data_dir, organism)
        file_path = os.path.join(organism_dir, f"{organism}.json")
        network_file = File(path=file_path)
 
        proto = RndExplorerProto()
        proto.input["network_file"] = network_file

        def _on_end(*args, **kwargs):
            f = proto.output["rnd_explorer_file"]
            result_dir = os.path.join(organism_dir, 'rnd_explore')
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)
                
            print("Fluxes:")
            print("------------")
            print(f.render__flux_ranges__as_table())
            file_path = os.path.join(result_dir, "flux.csv")
            with open(file_path, 'w') as fp:
                fp.write( f.render__flux_ranges__as_table().to_csv() )

            print("SV:")
            print("------------")
            print(f.render__sv_ranges__as_table())
            file_path = os.path.join(result_dir, "sv.csv")
            with open(file_path, 'w') as fp:
                fp.write( f.render__sv_ranges__as_table().to_csv() )
                
        e = proto.create_experiment(study=GTest.study, user=GTest.user)
        e.on_end(_on_end)
        asyncio.run( e.run() )