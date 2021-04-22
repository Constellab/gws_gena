
import os, json
import unittest

from gws.settings import Settings
settings = Settings.retrieve()
settings.use_prod_biota_db(True)

from gena.network import Network, Compound, Reaction
from gena.biomodel import Biomodel
from gena.context import Context
from biota.compound import Compound as BiotaCompound


class TestTwin(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Biomodel.drop_table()
        Context.drop_table()
        Network.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Biomodel.drop_table()
        Context.drop_table()
        Network.drop_table()
        settings.use_prod_biota_db(False)
        pass
    
    def test_context(self):
        data_dir = settings.get_dir("gena:testdata_dir")
        file_path = os.path.join(data_dir, "toy_context.json")
        
        with open(file_path) as f:
            data = json.load(f)
            ctx = Context.from_json(data)
        
        _json = ctx.dumps(stringify=True, prettify=True)
        print(_json)        
        print(ctx.to_json())

        self.assertEqual( data["measures"][1], ctx.dumps()[1] )
        self.assertEqual( data["measures"][0].get("confidence_score"), 1.0 )
        self.assertEqual( ctx.dumps()[0].get("confidence_score"), 1.0 )