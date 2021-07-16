
import os, json
import unittest
import asyncio

from gws.unittest import GTest
from gws.settings import Settings
from gws.file import File
settings = Settings.retrieve()

from gena.compound import Compound 
from gena.reaction import Reaction 
from gena.network import Network from gena.context import Context
from gena.biomodel import BioModel
from gena.gap_find import GapFinder
from biota.base import DbManager as BiotaDbManager

class TestGapFinder(unittest.TestCase):
    
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
    
    def test_gap_finder(self):
        GTest.print("Test GapFinder")
        organism = "pcys"
        data_dir = settings.get_dir("gena:testdata_dir")
        organism_dir = os.path.join(data_dir, organism)
        file_path = os.path.join(organism_dir, f"{organism}.json")
        with open(file_path, 'r') as fp:
            json_data = json.load(fp)
        net = Network.from_json(json_data)
        proc = GapFinder()
        proc.input["network"] = net

        def _on_end(*args, **kwargs):
            result = proc.output["result"]
            result_dir = os.path.join(organism_dir, 'gap_find')
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)

            print("Compounds:")
            print("------------")
            print(result.render__compounds__as_table())
            file_path = os.path.join(result_dir, "compounds.csv")
            with open(file_path, 'w') as fp:
                fp.write( result.render__compounds__as_table().to_csv() )

            print("Reactions:")
            print("------------")
            print(result.render__reactions__as_table())
            file_path = os.path.join(result_dir, "reactions.csv")
            with open(file_path, 'w') as fp:
                fp.write( result.render__reactions__as_table().to_csv() )

            print("Pathways:")
            print("------------")
            print(result.render__pathways__as_table())
            file_path = os.path.join(result_dir, "pathways.csv")
            with open(file_path, 'w') as fp:
                fp.write( result.render__pathways__as_table().to_csv() )

        e = proc.create_experiment(user=GTest.user, study=GTest.study)
        e.on_end(_on_end)
        asyncio.run( e.run() )

