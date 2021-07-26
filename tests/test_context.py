
import asyncio
import os, json
import unittest

from gws.settings import Settings
settings = Settings.retrieve()

from gena.network import Network, Compound, Reaction
from gena.biomodel import BioModel
from gena.context import Context, ContextBuilder
from gena.data import FluxData

from biota.compound import Compound as BiotaCompound
from biota.base import DbManager as BiotaDbManager

from gws.unittest import GTest

class TestContext(unittest.TestCase):
    
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

    def test_context(self):
        GTest.print("Test Context")
        data_dir = settings.get_dir("gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")
        file_path = os.path.join(data_dir, "toy_context.json")
        
        with open(file_path) as f:
            data = json.load(f)
            ctx = Context.from_json(data)
        
        _json = ctx.dumps()
        print(_json)        
        print(ctx.to_json())

        self.assertEqual( data["measures"][1], ctx.dumps()[1] )
        self.assertEqual( data["measures"][0].get("confidence_score"), 1.0 )
        self.assertEqual( ctx.dumps()[0].get("confidence_score"), 1.0 )
        
        
    def test_context_builder(self):
        GTest.print("Test Context Builder")
        data_dir = settings.get_dir("gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")
        
        # flux
        file_path = os.path.join(data_dir, "toy_flux_data.csv")
        flux_data = FluxData._import(file_path, delimiter=",")
        
        # network
        file_path = os.path.join(data_dir, "toy_network.json")
        with open(file_path) as f:
            data = json.load(f)
            net = Network.from_json(data)
        
        # experiment
        builder = ContextBuilder()
        builder.input["network"] = net
        builder.input["flux_data"] = flux_data
        
        def _on_end(*args, **kwargs):
            ctx = builder.output["context"]
            #print(ctx.to_json(prettify=True,stringify=True))
            expected_measures = [
                {
                    "id": "measure_R1_ex",
                    "name": "",
                    "variables": [
                        {
                            "reference_id": "R1_ex",
                            "reference_type": "reaction",
                            "coefficient": 1.0
                        }
                    ],
                    "lower_bound": 0.0,
                    "upper_bound": 40.0,
                    "target": 30.0,
                    "confidence_score": 1.0
                }
            ]
            
            self.assertEqual(ctx.dumps(), expected_measures)
            
        e = builder.create_experiment(study=GTest.study, user=GTest.user)
        e.on_end(_on_end)
        asyncio.run( e.run() )