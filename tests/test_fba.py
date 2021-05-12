
import asyncio
import os, json
import unittest

from gws.model import *
from gws.settings import Settings
settings = Settings.retrieve()

from gena.network import Network
from gena.context import Context
from gena.biomodel import Biomodel
from gena.fba import FluxAnalyzer, FluxAnalyzerResult
from gws.unittest import GTest

from biota.base import DbManager as BiotaDbManager

class TestFba(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        tables = ( Biomodel, Context, Network, Experiment, Study, User, Activity, ProgressBar, FluxAnalyzer, FluxAnalyzerResult, )
        GTest.drop_tables(tables)
        
        GTest.init()
        BiotaDbManager.use_prod_db(True)

    @classmethod
    def tearDownClass(cls):
        BiotaDbManager.use_prod_db(False)
        tables = ( Biomodel, Context, Network, Experiment, Study, User, Activity, ProgressBar, FluxAnalyzer, FluxAnalyzerResult, )
        GTest.drop_tables(tables)

    def test_fba(self):
        data_dir = settings.get_dir("gena:testdata_dir")
        
        file_path = os.path.join(data_dir, "toy_network.json")
        with open(file_path) as f:
            data = json.load(f)
            net = Network.from_json(data)
        
        file_path = os.path.join(data_dir, "toy_context.json")
        with open(file_path) as f:
            data = json.load(f)
            ctx = Context.from_json(data)
        
        bio = Biomodel()
        bio.add_network(net)
        bio.add_context(ctx, related_network=net)
        bio.save()

        fba = FluxAnalyzer()
        fba.set_param("least_energy_weight", 0)
        fba.set_param("number_of_randomizations", 1)
        fba.input["biomodel"] = bio
        
        def _on_end(*args, **kwargs):
            f = fba.output["file"]
            print( f.extension )
            print( f.to_json(read_content=True, prettify=True, stringify=True) )
            
            file_path = os.path.join(data_dir, "flat_toy_result.json")
            with open(file_path) as fp:
                expected_result_content = json.load(fp)            
                result_content = f.to_json(read_content=True)["data"]["content"]
                self.assertEqual( result_content, expected_result_content  )
            
            #print(f.view__stoich_matrix__as_csv())
            #print(f.view__solver_success__as_csv())
            #print(f.view__ker_of_identif__as_csv())
            #print(f.view__ker_of_intern_stoich__as_csv())
            #print(f.view__sv_distrib__as_csv())
            #print(f.view__sv_ranges__as_csv())
            print(f.view__flux_distrib__as_csv())
            print(f.view__flux_ranges__as_csv())
            
            print(f.view__feasible_fluxes__as_csv())
            
            
        e = fba.create_experiment(study=GTest.study, user=GTest.user)
        e.on_end(_on_end)
        asyncio.run( e.run() )