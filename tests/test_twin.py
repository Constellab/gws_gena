
import os, json
import unittest
from pandas import DataFrame
import pandas as pd

from gws_core import Settings, GTest
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_gena import Network
from gws_gena import Twin, FlatTwin, TwinContext
from gws_gena.twin.twin_service import MetaTwinService

settings = Settings.retrieve()

class TestTwin(BaseTestCaseUsingFullBiotaDB):

    def test_small_twin(self):
        self.print("Test Twin")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        
        file_path = os.path.join(data_dir, "small_net.json")
        with open(file_path) as f:
            data = json.load(f)
            net = Network.from_json(data)
            net2 = Network.from_json(data)
        
        file_path = os.path.join(data_dir, "small_context.json")
        with open(file_path) as f:
            data = json.load(f)
            ctx = TwinContext.from_json(data)
            ctx2 = TwinContext.from_json(data)
        
        bio = Twin()
        bio.add_network(net)
        bio.add_context(ctx, related_network=net)
        
        # export as json
        _json = bio.dumps(deep=True)
        #print(_json)
        
        self.assertRaises(Exception, bio.add_network, net)
        file_path = os.path.join(data_dir, "small_flat_twin.json")
        with open(file_path, 'w') as f:
            json.dump(bio.flatten(), f)
            
        file_path = os.path.join(data_dir, "small_flat_twin.json")
        with open(file_path) as f:
            data = json.load(f)
            print(data)
            self.assertEqual(bio.flatten(), data)
   
        flat_bio = FlatTwin.from_flat_dict(bio.flatten())
        problem = MetaTwinService.create_fba_problem(flat_bio)

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

    def test_toy_twin(self):
        self.print("Test Toy Twin")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")

        file_path = os.path.join(data_dir, "toy.json")
        with open(file_path) as f:
            data = json.load(f)
            net = Network.from_json(data)
            #net2 = Network.from_json(data)
        
        file_path = os.path.join(data_dir, "toy_context.json")
        with open(file_path) as f:
            data = json.load(f)
            ctx = TwinContext.from_json(data)
            #ctx2 = TwinContext.from_json(data)
        
        bio = Twin()
        bio.add_network(net)
        bio.add_context(ctx, related_network=net)
        
        flat_bio = FlatTwin.from_flat_dict(bio.flatten())
        problem = MetaTwinService.create_fba_problem(flat_bio)

        print('--- S_full ---')
        print(problem["S"])

        print('--- C ---')
        print(problem["C"])

        print('--- b ---')
        print(problem["b"])

        print('--- S_intra ---')        
        Si = MetaTwinService.create_steady_stoichiometric_matrix(flat_bio)
        #Si = MetaTwinService.extract_intracell_stoichiometric_matrix(problem["S"])
        print(Si)

        print('--- S_extra ---')
        Se = MetaTwinService.create_non_steady_stoichiometric_matrix(flat_bio)
        #Se = MetaTwinService.extract_extracell_stoichiometric_matrix(problem["S"])
        print(Se)

        print('--- Ker(S_intra) ---')
        K = MetaTwinService.compute_nullspace(Si)
        print(K)

        print('--- Ker( [S_intra; C] ) ---')
        K = MetaTwinService.compute_nullspace( pd.concat([Si, problem["C"]]) )
        print(K)