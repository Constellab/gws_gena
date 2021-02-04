
import os, json
import unittest

from gws.settings import Settings
settings = Settings.retrieve()
settings.use_prod_biota_db(True)

from gena.twin import Compound, Reaction, Twin
from gena.context import Context
from biota.db.compound import Compound as BiotaCompound


class TestTwin(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Twin.drop_table()
        Twin.create_table()
        pass

    @classmethod
    def tearDownClass(cls):
        settings.use_prod_biota_db(False)
        pass
    
    def test_context(self):
        data_dir = settings.get_dir("gena:testdata_dir")
        file_path = os.path.join(data_dir, "toy_phenotype.json")
        
        with open(file_path) as f:
            data = json.load(f)
            ctx = Context.from_json(data)
        
        _json = ctx.dumps(stringify=True, prettify=True)
        print(_json)        
        print(ctx.as_json())

        self.assertEqual( data["measures"][1], ctx.dumps()[1] )
        self.assertEqual( data["measures"][0].get("confidence_score"), None )
        self.assertEqual( ctx.dumps()[0].get("confidence_score"), 1.0 )