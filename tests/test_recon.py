
import os, json
import unittest
import asyncio

from gws.settings import Settings
from gws.model import *
from gws.unittest import GTest

settings = Settings.retrieve()

from gena.network import *
from gena.context import Context
from gena.biomodel import Biomodel
from gena.recon import DraftRecon
from gena.gapfill import GapFiller 
from gena.merge import NetworkMerger
from gena.data import *

from biota.base import DbManager as BiotaDbManager

class TestRecon(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        tables = ( Resource, Biomodel, Context, Network, DraftRecon, ECData, MediumData, Experiment, Study, User, Activity, ProgressBar, )
        GTest.drop_tables(tables)
        GTest.init()
        BiotaDbManager.use_prod_db(True)

    @classmethod
    def tearDownClass(cls):
        BiotaDbManager.use_prod_db(False)
        tables = ( Biomodel, Context, Network, DraftRecon, ECData, MediumData, Experiment, Study, User, Activity, ProgressBar, )
        GTest.drop_tables(tables)        
        

    def test_recon(self):
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

        gapfiller = GapFiller()
        gapfiller.set_param('tax_id', "4753")    #fungi 
        #gapfiller.set_param('tax_id', "2759")    #eukaryota
        gapfiller.set_param('biomass_and_medium_gaps_only', True)
        

        file_path = os.path.join(data_dir, "recon_addon.json")
        net_loader = NetworkLoader()
        net_loader.set_param("file_path", file_path)
        merger = NetworkMerger()
        
        proto = Protocol(
            processes = {
                "ec_loader": ec_loader,
                "medium_loader": medium_loader,
                "biomass_loader": biomass_loader,
                "recon": recon,
                "gapfiller": gapfiller,
                "merger": merger,
                "net_loader": net_loader
            },
            connectors = [
                ec_loader>>"data" | recon<<"ec_data",
                biomass_loader>>"data" | recon<<"biomass_data",
                medium_loader>>"data" | recon<<"medium_data",
                recon>>"network" | merger<<"network_1",
                net_loader>>"data" | merger<<"network_2",
                merger>>"network" | gapfiller<<"network",
            ]
        )
        
        def _export_network(net, file_name):
            #file_path = os.path.join(data_dir, file_name+"_net.json")
            #with open(file_path, 'w') as f:
            #    json.dump(net.to_json(), f)

            file_path = os.path.join(data_dir, file_name+"_net.csv")
            with open(file_path, 'w') as f:
                f.write(net.to_csv())
                
            file_path = os.path.join(data_dir, file_name+"_stats.csv")
            with open(file_path, 'w') as f:
                table = net.view__compound_stats__as_table()
                f.write(table.to_csv())
            
            file_path = os.path.join(data_dir, file_name+"_gaps.csv")
            with open(file_path, 'w') as f:
                table = net.view__gaps__as_table()
                f.write(table.to_csv())
            
        def _on_end(*args, **kwargs):
            net = recon.output['network']
            file_name = "recon"
            _export_network(net, file_name)
            
            #net = gapfiller.output['network']
            #file_name = "gapfill"
            #_export_network(net, file_name)
            
            net = merger.output['network']
            file_name = "merger"
            _export_network(net, file_name)
            
            
            
        e = proto.create_experiment( study=GTest.study, user=GTest.user )
        e.on_end( _on_end )
        asyncio.run( e.run() )
        