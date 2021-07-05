
import asyncio
import os, json
import unittest

from gws.model import *
from gws.settings import Settings
from gws.unittest import GTest
from gws.file import File
settings = Settings.retrieve()

from gena.network import Network
from gena.context import Context
from gena.biomodel import BioModel
from gena.check import FluxChecker, FluxCheckerResult
from gena.check_proto import FluxCheckerProto

from biota.base import DbManager as BiotaDbManager

class TestFba(unittest.TestCase):
    
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

    def test_checker_proto(self):
        GTest.print("Test FluxCheckerProto")
        
        data_dir = settings.get_dir("gena:testdata_dir")
        file_name = "ecoli/ecoli-core"
        #file_name = "dist/olga_net"

        file_path = os.path.join(data_dir, file_name+".json")
        network_file = File(path=file_path)
 
        proto = FluxCheckerProto()
        proto.input["network_file"] = network_file

        def _on_end(*args, **kwargs):
            f = proto.output["flux_checker_file"]
            
            print("Fluxes:")
            print("------------")
            print(f.render__flux_ranges__as_table())
            file_path = os.path.join(data_dir, file_name+"_flux.csv")
            with open(file_path, 'w') as fp:
                fp.write( f.render__flux_ranges__as_table().to_csv() )

            print("SV:")
            print("------------")
            print(f.render__sv_ranges__as_table())
            file_path = os.path.join(data_dir, file_name+"_sv.csv")
            with open(file_path, 'w') as fp:
                fp.write( f.render__sv_ranges__as_table().to_csv() )
                
        e = proto.create_experiment(study=GTest.study, user=GTest.user)
        e.on_end(_on_end)
        asyncio.run( e.run() )