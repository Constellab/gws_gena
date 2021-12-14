
import json
import os
import unittest

import numpy
import pandas as pd
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, GTest, Settings
from gws_gena import FlatTwin, Network, Twin, TwinContext, TwinHelper
from pandas import DataFrame

settings = Settings.retrieve()


class TestTwin(BaseTestCaseUsingFullBiotaDB):

    def test_small_twin(self):
        # return
        self.print("Test Twin")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "small_net")

        file_path = os.path.join(data_dir, "small_net.json")
        net = Network.import_from_path(
            File(path=file_path),
            params=ConfigParams()
        )
        file_path = os.path.join(data_dir, "small_context.json")
        ctx = TwinContext.import_from_path(
            File(path=file_path),
            params=ConfigParams()
        )

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
            self.assertEqual(twin.dumps_flat(), data)

        flat_twin = twin.flatten()
        problem = TwinHelper.create_fba_problem(flat_twin)

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
        # return
        self.print("Test Toy Twin")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")

        net = Network.import_from_path(
            File(path=os.path.join(data_dir, "toy.json")),
            ConfigParams()
        )
        ctx = TwinContext.import_from_path(
            File(path=os.path.join(data_dir, "toy_context.json")),
            ConfigParams()
        )
        twin = Twin()
        twin.add_network(net)
        twin.add_context(ctx, related_network=net)

        flat_twin = twin.flatten()
        problem = TwinHelper.create_fba_problem(flat_twin)

        print('\n--- S_full ---')
        print(problem["S"])

        print('\n--- C ---')
        print(problem["C"])

        print('\n--- b ---')
        print(problem["b"])

        print('\n--- S_intra ---')
        Si = TwinHelper.create_steady_stoichiometric_matrix(flat_twin)
        self.assertEqual(Si.shape, (5, 7,))
        print(Si)

        print('\n--- S_extra ---')
        Se = TwinHelper.create_non_steady_stoichiometric_matrix(flat_twin)
        self.assertEqual(Se.shape, (5, 7,))
        print(Se)

        print('\n--- Ker(S_intra) ---')
        K = TwinHelper.compute_nullspace(Si)
        self.assertEqual(K.shape, (7, 2,))
        expected_K = numpy.array([
            [-0.428766, 0.204856],
            [0.469203, 0.194713],
            [0.040437, 0.399569],
            [-0.428766, 0.204856],
            [-0.428766, 0.204856],
            [0.469203, 0.194713],
            [0.080873, 0.799138]
        ])
        self.assertTrue(numpy.all(numpy.isclose(K.values, expected_K, atol=1e-3)))
        print(K)

        print('\n--- Ker( [S_intra; C] ) ---')
        K = TwinHelper.compute_nullspace(pd.concat([Si, problem["C"]]))
        self.assertEqual(K.shape, (7, 0,))
        print(K)

        print('\n--- EFM ---')
        efm = TwinHelper.compute_elementary_flux_modes(flat_twin)
        self.assertEqual(efm.shape, (7, 2,))
        expected_efm = numpy.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
            [1.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [2.0, 2.0]
        ])
        self.assertTrue(numpy.all(numpy.isclose(efm.values, expected_efm)))
        print(efm)

        print('\n--- Input S ---')
        S = TwinHelper.create_input_stoichiometric_matrix(flat_twin)
        print(S)

        print('\n--- Output S ---')
        S = TwinHelper.create_output_stoichiometric_matrix(flat_twin)
        print(S)

        print('\n--- Reduced Twin ---')
        mat = TwinHelper.compute_reduced_matrices(flat_twin)
        print(mat["K"])
