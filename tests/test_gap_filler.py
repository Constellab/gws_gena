
import os, json
import unittest
import asyncio

from gws.unittest import GTest
from gws.settings import Settings
from gws.file import File
settings = Settings.retrieve()

from gena.compound import Compound 
from gena.reaction import Reaction 
from gena.network import Network 
from gena.context import Context
from gena.biomodel import BioModel
from gena.gap_fill import GapFiller
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
        GTest.print("Test GapFiller")
        def _gap_fill(organism):
            data_dir = settings.get_dir("gena:testdata_dir")
            file_path = os.path.join(data_dir, organism, f"{organism}.json")
            with open(file_path, 'r') as fp:
                json_data = json.load(fp)
            net = Network.from_json(json_data)

            nb_gaps = 0
            info = net._get_gap_info()
            for k in info["compounds"]:
                if info["compounds"][k]["is_gap"]:
                    nb_gaps += 1
            print(f"Total number of gaps: {nb_gaps} over {len(info['compounds'])} compounds")

            gapfiller = GapFiller()
            if organism == "pcys":
                gapfiller.set_param('tax_id', "4751")    #fungi
            else:
                gapfiller.set_param('tax_id', "562")    #ecoli
                #gapfiller.set_param('tax_id', "2")    #bacteria

            gapfiller.set_param('add_sink_reactions', True)
            gapfiller.input["network"] = net

            def _on_end(*args, **kwargs):
                result = gapfiller.output["network"]
                result_dir = os.path.join(data_dir, 'gap_fill')
                if not os.path.exists(result_dir):
                    os.makedirs(result_dir)
                
                file_path = os.path.join(result_dir, f"{organism}.json")
                with open(file_path, 'w') as fp:
                    json.dump(result.to_json(), fp)

                # file_path = os.path.join(result_dir, f"{organism}.json")
                # with open(file_path, 'r') as fp:
                #     expected_json = json.load(fp)
                #     self.assertEquals(result.to_json(), expected_json)

            e = gapfiller.create_experiment(user=GTest.user, study=GTest.study)
            e.on_end(_on_end)
            asyncio.run( e.run() )

        #_gap_fill("pcys")
        _gap_fill("ecoli_gap")

