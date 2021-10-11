
import os, json
import unittest
from pandas import DataFrame
import pandas as pd
import numpy

from gws_core import Settings, GTest
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_gena import Network
from gws_gena import Twin, FlatTwin, TwinContext
from gws_gena.twin.twin_service import TwinService

settings = Settings.retrieve()

class TestTwin(BaseTestCaseUsingFullBiotaDB):

    def test_small_twin(self):
        return
        self.print("Test Twin")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "small_net")

        file_path = os.path.join(data_dir, "small_net.json")
        net = Network.import_from_path(file_path)

        file_path = os.path.join(data_dir, "small_context.json")
        ctx = TwinContext.import_from_path(file_path)

        twin = Twin()
        twin.add_network(net)
        twin.add_context(ctx, related_network=net)
        
        self.assertRaises(Exception, twin.add_network, net)
        file_path = os.path.join(data_dir, "small_flat_twin.json")
        with open(file_path, 'w') as f:
            json.dump(twin.dumps_flat(), f)
            
        file_path = os.path.join(data_dir, "small_flat_twin.json")
        with open(file_path) as f:
            data = json.load(f)
            print(data)
            self.assertEqual(twin.dumps_flat(), data)
   
        flat_twin = twin.flatten()
        problem = TwinService.create_fba_problem(flat_twin)

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
        return
        self.print("Test Toy Twin")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")

        net = Network.import_from_path(os.path.join(data_dir, "toy.json"))
        ctx = TwinContext.import_from_path(os.path.join(data_dir, "toy_context.json"))

        twin = Twin()
        twin.add_network(net)
        twin.add_context(ctx, related_network=net)
        
        flat_twin = twin.flatten()
        problem = TwinService.create_fba_problem(flat_twin)

        print('\n--- S_full ---')
        print(problem["S"])

        print('\n--- C ---')
        print(problem["C"])

        print('\n--- b ---')
        print(problem["b"])

        print('\n--- S_intra ---')        
        Si = TwinService.create_steady_stoichiometric_matrix(flat_twin)
        self.assertEqual(Si.shape, (5,7,))
        print(Si)

        print('\n--- S_extra ---')
        Se = TwinService.create_non_steady_stoichiometric_matrix(flat_twin)
        self.assertEqual(Se.shape, (5,7,))
        print(Se)

        print('\n--- Ker(S_intra) ---')
        K = TwinService.compute_nullspace(Si)
        self.assertEqual(K.shape, (7,2,))
        expected_K = numpy.array([
            [-0.428766, 0.204856],
            [0.469203, 0.194713],
            [0.040437, 0.399569],
            [-0.428766, 0.204856],
            [-0.428766, 0.204856],
            [0.469203, 0.194713],
            [0.080873, 0.799138]
        ])
        self.assertTrue( numpy.all(numpy.isclose(K.values,expected_K, atol=1e-3)) )
        print(K)

        print('\n--- Ker( [S_intra; C] ) ---')
        K = TwinService.compute_nullspace( pd.concat([Si, problem["C"]]) )
        self.assertEqual(K.shape, (7,0,))
        print(K)

        print('\n--- EFM ---')
        efm = TwinService.compute_elementary_flux_modes(flat_twin)
        self.assertEqual(efm.shape, (7,2,))
        expected_efm = numpy.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
            [1.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [2.0, 2.0]
        ])
        self.assertTrue( numpy.all(numpy.isclose(efm.values,expected_efm)) )
        print(efm)

        print('\n--- Input S ---')
        S = TwinService.compute_input_stoichiometric_matrix(flat_twin)
        print(S)

        print('\n--- Output S ---')
        S = TwinService.compute_output_stoichiometric_matrix(flat_twin)
        print(S)


        print('\n--- Reduced Twin ---')
        K = TwinService.reduce_twin(flat_twin)
        print(K)

    def test_bastin_twin(self):
        self.print("Test Toy Twin")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "bastin")

        net = Network.import_from_path(os.path.join(data_dir, "bastin_network.json"))
        ctx = TwinContext.import_from_path(os.path.join(data_dir, "bastin_context.json"))

        twin = Twin()
        twin.add_network(net)
        twin.add_context(ctx, related_network=net)
        
        flat_twin = twin.flatten()

        print('\n--- EFM Bastin & Provost ---')
        efm = TwinService.compute_elementary_flux_modes(flat_twin)
        print(efm)

        print('\n--- Reduced Bastin & Provost ---')
        K = TwinService.reduce_twin(flat_twin)
        print(K)