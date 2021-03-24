
import os, json
import unittest
import asyncio

from gws.settings import Settings
from gws.model import Study
settings = Settings.retrieve()
settings.use_prod_biota_db(True)

from gena.network import Network
from gena.context import Context
from gena.biomodel import Biomodel
from gena.data import ECData
from gena.recon import DraftRecon

class TestRecon(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Biomodel.drop_table()
        Context.drop_table()
        Network.drop_table()
        DraftRecon.drop_table()
        ECData.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Biomodel.drop_table()
        Context.drop_table()
        Network.drop_table()
        settings.use_prod_biota_db(False)
        pass

    def test_draft_recon(self):
        data_dir = settings.get_dir("gena:testdata_dir")
        file_path = os.path.join(data_dir, "ec_data.csv")
        
        ec_data = ECData._import(file_path, ec_column_name="EC Number")
        ec_data.save()
        
        bm = DraftRecon()
        bm.input['ec_data'] = ec_data
        
        def _on_end(*args, **kwargs):
            net = bm.output['network']
            print(net.as_json(stringify=True, prettify=True))
            print(net.as_str())
            
            file_path = os.path.join(data_dir, "recon_net.csv")
            with open(file_path, 'r') as f:
                self.assertEqual( f.read(), net.as_csv() )
             
            #with open(file_path, 'w') as f:
            #    f.write(net.as_csv())
            
        e = bm.create_experiment( study =Study.get_default_instance() )
        e.on_end( _on_end )
        
        asyncio.run( e.run() )
        