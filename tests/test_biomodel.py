
import os, json
import unittest

from gws.settings import Settings
settings = Settings.retrieve()

from gena.network import Network
from gena.context import Context
from gena.biomodel import BioModel

from biota.base import DbManager as BiotaDbManager

class TestBioModel(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        BioModel.drop_table()
        Context.drop_table()
        Network.drop_table()
        BiotaDbManager.use_prod_db(True)

    @classmethod
    def tearDownClass(cls):
        BiotaDbManager.use_prod_db(False)
        BioModel.drop_table()
        Context.drop_table()
        Network.drop_table()

    def test_biomodel(self):
        data_dir = settings.get_dir("gena:testdata_dir")
        
        file_path = os.path.join(data_dir, "small.json")
        with open(file_path) as f:
            data = json.load(f)
            net = Network.from_json(data)
            net2 = Network.from_json(data)
        
        file_path = os.path.join(data_dir, "toy_context.json")
        with open(file_path) as f:
            data = json.load(f)
            ctx = Context.from_json(data)
            ctx2 = Context.from_json(data)
        
        bio = BioModel()
        bio.add_network(net)
        bio.add_context(ctx, related_network=net)
        
        # export as json
        _json = bio.dumps(expand=True, prettify=True, stringify=True)
        #print(_json)
        
        self.assertRaises(Exception, bio.add_network, net)
        #file_path = os.path.join(data_dir, "flat_toy_biomodel.json")
        #with open(file_path, 'w') as f:
        #    json.dump(bio.flatten(), f)
            
        file_path = os.path.join(data_dir, "flat_toy_biomodel.json")
        with open(file_path) as f:
            data = json.load(f)
            print(data)
            self.assertEqual(bio.flatten(), data)