
import asyncio
import os, json
import unittest

from gws.model import *
from gws.settings import Settings
from gws.file import File
from gws.unittest import GTest

settings = Settings.retrieve()

from gena.network import Network
from gena.context import Context
from gena.biomodel import BioModel
from gena.fba import FluxAnalyzer, FluxAnalyzerResult
from gena.proto.fba import FluxAnalyzerProto

from biota.base import DbManager as BiotaDbManager

class TestFba(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        tables = ( 
            BioModel, Context, Network, 
            Experiment, Study, User, Activity, 
            ProgressBar, FluxAnalyzer, FluxAnalyzerResult, 
        )
        GTest.drop_tables(tables)
        
        GTest.init()
        BiotaDbManager.use_prod_db(True)

    @classmethod
    def tearDownClass(cls):
        BiotaDbManager.use_prod_db(False)
        tables = ( 
            BioModel, Context, Network, 
            Experiment, Study, User, Activity, 
            ProgressBar, FluxAnalyzer, FluxAnalyzerResult, 
        )
        GTest.drop_tables(tables)

    def test_fba(self):
        GTest.print("Test FluxAnalyzerProto")
        data_dir = settings.get_dir("gena:testdata_dir")

        proto = FluxAnalyzerProto()
        
        file_path = os.path.join(data_dir, "toy_network.json")
        network_file = File(path=file_path)
        file_path = os.path.join(data_dir, "toy_context.json")
        ctx_file = File(path=file_path)

        proto.input["network_file"] = network_file
        proto.input["context_file"] = ctx_file

        fba = proto.get_flux_analyzer()
        fba.set_param("least_energy_weight", 0)
        fba.set_param("number_of_randomizations", 1)
        fba.set_param("use_hard_bounds", True)
        fba.set_param("verbose", True)

        def _on_end(*args, **kwargs):
            f = proto.output["flux_analyzer_file"]
            print( f.extension )
            print( f.to_json(read_content=True, prettify=True, stringify=True) )
            
            file_path = os.path.join(data_dir, "flat_toy_result.json")
            
            #with open(file_path, 'w') as fp:
            #    result_content = f.to_json(read_content=True)["data"]["content"]
            #    json.dump(result_content, fp)
                
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
            print(f.render__flux_distrib__as_table())
            print(f.render__flux_ranges__as_table())
            #print(f.render__feasible_fluxes__as_table())

            bio = proto.output["annotated_biomodel"]
            print(bio.dumps(expand=True))
        
        e = proto.create_experiment(study=GTest.study, user=GTest.user)
        e.on_end(_on_end)
        asyncio.run( e.run() )
