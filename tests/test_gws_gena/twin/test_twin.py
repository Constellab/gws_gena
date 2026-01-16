import os

import numpy
import pandas as pd
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File
from gws_gena import ContextImporter, DataProvider, NetworkImporter, Twin, TwinHelper


class TestTwin(BaseTestCaseUsingFullBiotaDB):
    def test_small_twin(self):
        # return
        self.print("Test Twin")
        data_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(data_dir, "small_net")

        file_path = os.path.join(data_dir, "small_net.json")
        net = NetworkImporter.call(
            File(path=file_path), params={"skip_orphans": True, "add_biomass": True}
        )

        def do_test(context_name):
            file_path = os.path.join(data_dir, f"{context_name}.json")
            ctx = ContextImporter.call(File(path=file_path), params={})

            twin = Twin()
            twin.add_network(net)
            twin.add_context(ctx, related_network=net)

            self.assertRaises(Exception, twin.add_network, net)
            self.assertEqual(twin.dumps_flat(), twin.dumps_flat())

            # twin2 = FlatTwin.loads(twin.dumps_flat())
            # self.print(twin2.dumps_flat())
            # self.assertEqual(twin2.dumps_flat(), twin.dumps_flat())

            # file_path = os.path.join(data_dir, "small_flat_twin.json")
            # with open(file_path, "w", encoding="utf-8") as f:
            #     json.dump(twin.dumps_flat(), f)

            flat_twin = twin.flatten()
            problem = TwinHelper.create_fba_problem(flat_twin)

            # Test S
            # self.print(problem["S"])
            path = os.path.join(data_dir, "problem", context_name)
            if not os.path.exists(path):
                os.makedirs(path)
            expected_s = pd.read_csv(os.path.join(path, "S.csv"), index_col=0)
            S = problem["S"]
            expected_s = expected_s.loc[S.index, :]
            expected_s = expected_s.loc[:, S.columns]
            self.assertTrue(S.equals(expected_s))

            # Test C
            # self.print(problem["C"])
            expected_c = pd.read_csv(os.path.join(path, "C.csv"), index_col=0)
            self.assertTrue(problem["C"].equals(expected_c))

            # Test b
            # self.print(problem["b"])
            expected_b = pd.read_csv(os.path.join(path, "b.csv"), index_col=0)
            self.assertTrue(problem["b"].equals(expected_b))

            # Test r
            # self.print(problem["r"])
            # problem["r"].to_csv(os.path.join(path, "r.csv"))
            expected_r = pd.read_csv(os.path.join(path, "r.csv"), index_col=0)
            self.assertTrue(problem["r"].equals(expected_r))

        do_test("small_context")
        do_test("small_context_with_metpool")

    def test_toy_twin(self):
        return
        self.print("Test Toy Twin")
        data_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(data_dir, "toy")

        net = NetworkImporter.call(
            File(path=os.path.join(data_dir, "toy.json")), {"add_biomass": True}
        )
        ctx = ContextImporter.call(File(path=os.path.join(data_dir, "toy_context.json")), {})
        twin = Twin()
        twin.add_network(net)
        twin.add_context(ctx, related_network=net)

        flat_twin = twin.flatten()
        problem = TwinHelper.create_fba_problem(flat_twin)

        self.print("\n--- S_full ---")
        self.print(problem["S"])

        self.print("\n--- C ---")
        self.print(problem["C"])

        self.print("\n--- b ---")
        self.print(problem["b"])

        self.print("\n--- S_intra ---")
        Si = TwinHelper.create_steady_stoichiometric_matrix(flat_twin)
        self.assertEqual(
            Si.shape,
            (
                5,
                7,
            ),
        )
        self.print(Si)

        self.print("\n--- S_extra ---")
        Se = TwinHelper.create_non_steady_stoichiometric_matrix(flat_twin)
        self.assertEqual(
            Se.shape,
            (
                5,
                7,
            ),
        )
        self.print(Se)

        self.print("\n--- Ker(S_intra) ---")
        K = TwinHelper.compute_nullspace(Si)
        self.assertEqual(
            K.shape,
            (
                7,
                2,
            ),
        )
        expected_K = numpy.array(
            [
                [-0.428766, 0.204856],
                [0.469203, 0.194713],
                [0.040437, 0.399569],
                [-0.428766, 0.204856],
                [-0.428766, 0.204856],
                [0.469203, 0.194713],
                [0.080873, 0.799138],
            ]
        )
        self.assertTrue(numpy.all(numpy.isclose(K.values, expected_K, atol=1e-3)))
        self.print(K)

        self.print("\n--- Ker( [S_intra; C] ) ---")
        K = TwinHelper.compute_nullspace(pd.concat([Si, problem["C"]]))
        self.assertEqual(
            K.shape,
            (
                7,
                0,
            ),
        )
        self.print(K)

        self.print("\n--- EFM ---")
        efm = TwinHelper.compute_elementary_flux_modes(flat_twin)
        self.assertEqual(
            efm.shape,
            (
                7,
                2,
            ),
        )
        expected_efm = numpy.array(
            [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [2.0, 2.0]]
        )
        self.assertTrue(numpy.all(numpy.isclose(efm.values, expected_efm)))
        self.print(efm)

        self.print("\n--- Input S ---")
        S = TwinHelper.create_input_stoichiometric_matrix(flat_twin)
        self.print(S)

        self.print("\n--- Output S ---")
        S = TwinHelper.create_output_stoichiometric_matrix(flat_twin)
        self.print(S)

        self.print("\n--- Reduced Twin ---")
        mat = TwinHelper.compute_reduced_matrices(flat_twin)
        self.print(mat["K"])
