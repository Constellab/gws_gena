
import os, json
import unittest
import asyncio

from gws.settings import Settings
from gws.model import *
settings = Settings.retrieve()
settings.use_prod_biota_db(True)

from gena.network import Network
from gena.context import Context
from gena.biomodel import Biomodel
from gena.data import *
from gena.recon import DraftRecon

from gws.unittest import GTest

class TestRecon(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        tables = ( Biomodel, Context, Network, DraftRecon, ECData, MediumData, Experiment, Study, User, Activity, ProgressBar, )
        GTest.drop_tables(tables)
        GTest.init()
        pass

    @classmethod
    def tearDownClass(cls):
        tables = ( Biomodel, Context, Network, DraftRecon, ECData, MediumData, Experiment, Study, User, Activity, ProgressBar, )
        GTest.drop_tables(tables)
        settings.use_prod_biota_db(False)
        pass

    def test_draft_recon(self):
        data_dir = settings.get_dir("gena:testdata_dir")
        
        file_path = os.path.join(data_dir, "recon_ec_data.csv")
        ec_loader = ECLoader()
        ec_loader.set_param("file_path", file_path)
        ec_loader.set_param("ec_column_name", "EC Number")
        
        file_path = os.path.join(data_dir, "recon_medium.csv")
        medium_loader = MediumLoader()
        medium_loader.set_param("file_path", file_path)
        medium_loader.set_param("chebi_column_name", "Chebi ID")
        
        file_path = os.path.join(data_dir, "recon_biomass.csv")
        biomass_loader = BiomassLoader()
        biomass_loader.set_param("file_path", file_path)
        biomass_loader.set_param("biomass_column_name", "Biomass")
        biomass_loader.set_param("chebi_column_name", "Chebi ID")

        recon = DraftRecon()
        recon.set_param('tax_id', "263815")  #target pneumocyctis

        proto = Protocol(
            processes = {
                "ec_loader": ec_loader,
                "medium_loader": medium_loader,
                "biomass_loader": biomass_loader,
                "recon": recon
            },
            connectors = [
                ec_loader>>"data" | recon<<"ec_data",
                biomass_loader>>"data" | recon<<"biomass_data"
            ]
        )
        
        def _on_end(*args, **kwargs):
            net = recon.output['network']
            file_path = os.path.join(data_dir, "recon_net.json")
            with open(file_path, 'w') as f:
                json.dump(net.as_json(), f)
            
            
            #with open(file_path, 'r') as f:
            #    self.assertEqual( f.read(), net.as_csv() )
            
            file_path = os.path.join(data_dir, "recon_net.csv")
            with open(file_path, 'w') as f:
                f.write(net.as_csv())
            
        e = proto.create_experiment( study=GTest.study, user=GTest.user )
        e.on_end( _on_end )
        asyncio.run( e.run() )
        