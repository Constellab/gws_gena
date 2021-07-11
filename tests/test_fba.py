
import asyncio
import os, json
import unittest

from gws.settings import Settings
from gws.file import File
from gws.unittest import GTest

settings = Settings.retrieve()

from gena.network import Network
from gena.context import Context
from gena.biomodel import BioModel
from gena.fba import FBA, FBAResult
from gena.fba_proto import FBAProto

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

    def test_fba(self):
        GTest.print("Test FBAProto")
        data_dir = settings.get_dir("gena:testdata_dir")

        proto = FBAProto()
        
        file_path = os.path.join(data_dir, "toy_network.json")
        network_file = File(path=file_path)
        file_path = os.path.join(data_dir, "toy_context.json")
        ctx_file = File(path=file_path)

        proto.input["network_file"] = network_file
        proto.input["context_file"] = ctx_file

        fba = proto.get_fba()
        fba.set_param("least_energy_weight", 0)
        fba.set_param("number_of_randomizations", 1)
        fba.set_param("use_hard_bounds", True)
        fba.set_param("verbose", True)

        def _on_end(*args, **kwargs):
            f = proto.output["fba_file"]
            result_dir = os.path.join(data_dir, 'toy', 'fba')
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)

            file_path = os.path.join(result_dir, "result.json")
            # with open(file_path, 'w') as fp:
            #     result_content = f.to_json(shallow=False)["data"]["content"]
            #     json.dump(result_content, fp)
                
            with open(file_path) as fp:
                expected_result_content = json.load(fp)          
                result_content = f.to_json(shallow=False)["data"]["content"]
                self.assertEqual( result_content, expected_result_content  )
            
            #print(f.render__stoich_matrix__as_table())
            #print(f.render__solver_success__as_table())
            #print(f.render__ker_of_identif__as_table())
            #print(f.render__ker_of_intern_stoich__as_table())
            #print(f.render__sv_distrib__as_table())
            #print(f.render__sv_ranges__as_table())
            #print(f.render__flux_distrib__as_table())
            #print(f.render__flux_ranges__as_table())
            #print(f.render__feasible_fluxes__as_table())

            bio = proto.output["annotated_biomodel"]
            net = list(bio.networks.values())[0]
            tflux = net.render__total_flux__as_table()
            print(tflux)
            #print(bio.dumps(shallow=False))
        
        e = proto.create_experiment(study=GTest.study, user=GTest.user)
        e.on_end(_on_end)
        asyncio.run( e.run() )
