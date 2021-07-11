
import os, json
import unittest
from pandas import DataFrame
import pandas as pd

from gws.settings import Settings
from gws.unittest import GTest
settings = Settings.retrieve()

from gena.network import Network
from gena.context import Context
from gena.biomodel import BioModel

from biota.base import DbManager as BiotaDbManager

class TestBioModel(unittest.TestCase):
    
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

    # def test_small_biomodel__(self):
    #     data_dir = settings.get_dir("gena:testdata_dir")
        
    #     file_path = os.path.join(data_dir, "dist/olga.json")
    #     with open(file_path) as f:
    #         data = json.load(f)
    #         net = Network.from_json(data)
        
    #     file_path = os.path.join(data_dir, "dist/olga_context.json")
    #     with open(file_path) as f:
    #         data = json.load(f)
    #         ctx = Context.from_json(data)
        
    #     bio = BioModel()
    #     bio.add_network(net)
    #     bio.add_context(ctx, related_network=net)

    #     _json = bio.flatten()

    #     #print(net.dumps()["reactions"])

    def test_small_biomodel(self):
        GTest.print("Test BioModel")

        data_dir = settings.get_dir("gena:testdata_dir")
        
        file_path = os.path.join(data_dir, "small_net.json")
        with open(file_path) as f:
            data = json.load(f)
            net = Network.from_json(data)
            net2 = Network.from_json(data)
        
        file_path = os.path.join(data_dir, "small_context.json")
        with open(file_path) as f:
            data = json.load(f)
            ctx = Context.from_json(data)
            ctx2 = Context.from_json(data)
        
        bio = BioModel()
        bio.add_network(net)
        bio.add_context(ctx, related_network=net)
        
        # export as json
        _json = bio.dumps(shallow=False, prettify=True, stringify=True)
        #print(_json)
        
        self.assertRaises(Exception, bio.add_network, net)
        file_path = os.path.join(data_dir, "small_flat_biomodel.json")
        with open(file_path, 'w') as f:
            json.dump(bio.flatten(), f)
            
        file_path = os.path.join(data_dir, "small_flat_biomodel.json")
        with open(file_path) as f:
            data = json.load(f)
            print(data)
            self.assertEqual(bio.flatten(), data)
        
        from gena.service.biomodel_service import BioModelService
        flat_bio = bio.flatten(as_biomodel=True)
        problem = BioModelService.create_fba_problem(flat_bio)

        print(problem["S"])
        expected_S = DataFrame({
            'small_cell_EX_glc_D_e': [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
            'small_cell_GLNabc': [0.0, 1.0, -1.0, -1.0, 1.0, 0.0, 0.0],
            'small_cell_biomass': [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        }, index=[
            "glc_D_e", 
            "small_cell_gln_L_c", 
            "gln_L_e", 
            "small_cell_atp_c", 
            "small_cell_adp_c", 
            "small_cell_adp_n", 
            "small_cell_biomass_b"
            ]
        )
        self.assertTrue(problem["S"].equals(expected_S))
        
        print(problem["C"])
        expected_C = DataFrame({
            'small_cell_EX_glc_D_e': [1.0, 1.0], 
            'small_cell_GLNabc': [0.0, 2.0],
            'small_cell_biomass': [0.0, 0.0],
        }, index=[
            "Measure_1", 
            "Measure_2"
            ]
        )
        self.assertTrue(problem["C"].equals(expected_C))

        print(problem["b"])
        expected_B = DataFrame({
            'target': [30.0, 0.75], 
            'lb': [25.0, 0.5],
            'ub': [35.0, 1.0],
            'confidence_score': [1.0, 1.0],
        }, index=[
            "Measure_1", 
            "Measure_2"
            ]
        )
        self.assertTrue(problem["b"].equals(expected_B))

    def test_toy_biomodel(self):
        GTest.print("Test Toy BioModel")

        data_dir = settings.get_dir("gena:testdata_dir")
        
        file_path = os.path.join(data_dir, "toy_network.json")
        with open(file_path) as f:
            data = json.load(f)
            net = Network.from_json(data)
            #net2 = Network.from_json(data)
        
        file_path = os.path.join(data_dir, "toy_context.json")
        with open(file_path) as f:
            data = json.load(f)
            ctx = Context.from_json(data)
            #ctx2 = Context.from_json(data)
        
        bio = BioModel()
        bio.add_network(net)
        bio.add_context(ctx, related_network=net)
        
        from gena.service.biomodel_service import BioModelService
        flat_bio = bio.flatten(as_biomodel=True)
        problem = BioModelService.create_fba_problem(flat_bio)

        print('--- S_full ---')
        print(problem["S"])

        print('--- C ---')
        print(problem["C"])

        print('--- b ---')
        print(problem["b"])

        print('--- S_intra ---')        
        Si = BioModelService.create_steady_stoichiometric_matrix(flat_bio)
        #Si = BioModelService.extract_intracell_stoichiometric_matrix(problem["S"])
        print(Si)

        print('--- S_extra ---')
        Se = BioModelService.create_non_steady_stoichiometric_matrix(flat_bio)
        #Se = BioModelService.extract_extracell_stoichiometric_matrix(problem["S"])
        print(Se)

        print('--- Ker(S_intra) ---')
        K = BioModelService.compute_nullspace(Si)
        print(K)

        print('--- Ker( [S_intra; C] ) ---')
        K = BioModelService.compute_nullspace( pd.concat([Si, problem["C"]]) )
        print(K)