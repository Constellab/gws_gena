
import asyncio
import os, json
import unittest

from gws.settings import Settings
from gws.file import File
from gws.unittest import GTest

settings = Settings.retrieve()

from gena import Network
from gena import BioModel, Context
from gena.deprec.fba.fba import FBA, FBAResult
from gena.deprec.fba.proto.fba_proto import FBAProto

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

        def run_fba( organism, number_of_randomizations=1 ):
            proto = FBAProto()            
            organism_dir = os.path.join(data_dir, organism)
            file_path = os.path.join(organism_dir, f"{organism}.json")
            try:
                network_file = File.get(File.path == file_path)
            except:
                network_file = File(path=file_path)
            file_path = os.path.join(organism_dir, f"{organism}_context.json")
            try:
                ctx_file = File.get(File.path == file_path)
            except:
                ctx_file = File(path=file_path)

            proto.input["network_file"] = network_file
            proto.input["context_file"] = ctx_file

            fba = proto.get_fba()
            fba.set_param("number_of_randomizations", number_of_randomizations)
            fba.set_param("use_hard_bounds", True)
            fba.set_param("verbose", False)

            def _on_end(*args, **kwargs):
                result = proto.output["fba_result"]
                result_dir = os.path.join(organism_dir, 'fba_deprec', f'nrnd={number_of_randomizations}')
                if not os.path.exists(result_dir):
                    os.makedirs(result_dir)

                file_path = os.path.join(result_dir, "result.json")
                with open(file_path, 'w') as fp:
                    result_content = result.to_json(shallow=False)["data"]["content"]
                    json.dump(result_content, fp)
                
                file_path = os.path.join(result_dir, "result.json")
                with open(file_path) as fp:
                    expected_result_content = json.load(fp)          
                    result_content = result.to_json(shallow=False)["data"]["content"]
                    self.assertEqual( result_content, expected_result_content  )

                fluxes = result.render__flux_ranges__as_table()
                sv = result.render__flux_ranges__as_table()
                print(fluxes)
                print(sv)

                biomass_flux = fluxes.loc[["ecoli_BIOMASS_Ecoli_core_w_GAM"],:]
                print(biomass_flux)

            e = proto.create_experiment(study=GTest.study, user=GTest.user)
            e.on_end(_on_end)
            asyncio.run( e.run() )
        
        #run_fba( organism="toy", number_of_randomizations=1  )
        #run_fba( organism="toy", number_of_randomizations=100 )
        run_fba( organism="ecoli", number_of_randomizations=1000 )

        