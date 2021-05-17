
import asyncio
import os, json
import unittest

from gws.model import *
from gws.settings import Settings
settings = Settings.retrieve()

from gena.network import Network
from gena.context import Context
from gena.biomodel import Biomodel
from gena.check import FluxChecker, FluxCheckerResult
from gws.unittest import GTest

from biota.base import DbManager as BiotaDbManager

class TestFba(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        tables = ( Biomodel, Context, Network, Experiment, Study, User, Activity, ProgressBar, FluxChecker, FluxCheckerResult, )
        GTest.drop_tables(tables)
        GTest.init()
        BiotaDbManager.use_prod_db(True)


    @classmethod
    def tearDownClass(cls):
        BiotaDbManager.use_prod_db(False)
        tables = ( Biomodel, Context, Network, Experiment, Study, User, Activity, ProgressBar, FluxChecker, FluxCheckerResult, )
        GTest.drop_tables(tables)

    def test_check(self):
        data_dir = settings.get_dir("gena:testdata_dir")
        
        #file_name = "ecoli/ecoli-core"
        file_name = "dist/olga_net"
        
        file_path = os.path.join(data_dir, file_name+".json")
        with open(file_path) as f:
            data = json.load(f)
            net = Network.from_json(data)
        
        #file_path = os.path.join(data_dir, "toy_context.json")
        #with open(file_path) as f:
        #    data = json.load(f)
        #    ctx = Context.from_json(data)
        
        bio = Biomodel()
        bio.add_network(net)
        #bio.add_context(ctx, related_network=net)
        bio.save()

        fba = FluxChecker()
        fba.input["biomodel"] = bio
        fba.set_param("least_energy_weight", 0.001)
        
        if file_name == "ecoli/ecoli-core":
            fba.set_param("number_of_randomizations", 10)
            fba.set_param("verbose", False)
        else:
            fba.set_param("number_of_randomizations", 2)
            fba.set_param("verbose", True)
            
        fba.set_param("use_hard_bounds", True)
        fba.set_param("algorithm", "bfgs")
        
        
        def _on_end(*args, **kwargs):
            f = fba.output["file"]
            #print(f.view__flux_distrib__as_table())
            
            print("Fluxes:")
            print("------------")
            print(f.view__flux_ranges__as_table())
            file_path = os.path.join(data_dir, file_name+"_flux.csv")
            with open(file_path, 'w') as fp:
                fp.write( f.view__flux_ranges__as_table().to_csv() )
                
                
            print("SV:")
            print("------------")
            print(f.view__sv_ranges__as_table())
            file_path = os.path.join(data_dir, file_name+"_sv.csv")
            with open(file_path, 'w') as fp:
                fp.write( f.view__sv_ranges__as_table().to_csv() )
                
        e = fba.create_experiment(study=GTest.study, user=GTest.user)
        e.on_end(_on_end)
        asyncio.run( e.run() )