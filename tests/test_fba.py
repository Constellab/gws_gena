
import asyncio
import os, json
import unittest

from gws.model import Protocol, Study, Experiment
from gws.settings import Settings
settings = Settings.retrieve()
settings.use_prod_biota_db(True)

from gena.network import Network
from gena.context import Context
from gena.biomodel import Biomodel
from gena.fba import FluxAnalyzer
from gws.unittest import GTest

class TestFba(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Experiment.drop_table()
        Protocol.drop_table()
        Study.drop_table()
        Biomodel.drop_table()
        Context.drop_table()
        Network.drop_table()
        FluxAnalyzer.drop_table()
        GTest.init()
        pass

    @classmethod
    def tearDownClass(cls):
        Experiment.drop_table()
        Protocol.drop_table()
        Study.drop_table()
        Biomodel.drop_table()
        Context.drop_table()
        Network.drop_table()
        FluxAnalyzer.drop_table()
        settings.use_prod_biota_db(False)
        pass

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
        fba.input["biomodel"] = bio
        
        def _on_end(*args, **kwargs):
            f = fba.output["file"]
            print( f.extension )
            print( f.as_json(read_content=True, prettify=True, stringify=True) )
            
            file_path = os.path.join(data_dir, "flat_toy_result.json")
            with open(file_path) as fp:
                expected_result_content = json.load(fp)            
                result_content = f.as_json(read_content=True)["data"]["content"]
                self.assertEqual( result_content, expected_result_content  )
            
        
        e = fba.create_experiment(study=GTest.study, user=GTest.user)
        e.on_end(_on_end)
        asyncio.run( e.run() )