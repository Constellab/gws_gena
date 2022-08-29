import os

import numpy
import pandas
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import (ConfigParams, ExperimentService, File, GTest,
                      IExperiment, Settings, ViewTester)
from gws_gena import (Context, ContextImporter, FBAProto, Network,
                      NetworkImporter, Twin)

settings = Settings.retrieve()


class TestTwinAnnotator(BaseTestCaseUsingFullBiotaDB):

    async def test_twin_annotator(self):
        testdata_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(testdata_dir, "toy")
        organism_result_dir = os.path.join(testdata_dir, 'fba', "toy")

        solver="quad"
        relax_qssa=False

        experiment = IExperiment(FBAProto)
        proto = experiment.get_protocol()

        net = NetworkImporter.call(File(
            path=os.path.join(data_dir, "toy.json"))
        )
        ctx = ContextImporter.call(
            File(path=os.path.join(data_dir, "toy_context.json"))
        )

        proto.set_input("network", net)
        proto.set_input("context", ctx)

        fba = proto.get_process("fba")
        fba.set_param("solver", solver)

        await experiment.run()

        # test results
        result = proto.get_output("fba_result")
        twin = proto.get_output("annotated_twin")

        fluxes = result.get_fluxes_dataframe()
        sv = result.get_sv_dataframe()
        print(fluxes)
        print(sv)
        th, p = result.compute_zero_flux_threshold()
        print(f"sv_mean = {sv['value'].mean()}, sv_std = {sv['value'].std()}, sv_th={th}, sv_p = {p}")

        if solver == "quad":
            relax_dir = "relax" if relax_qssa else "no-relax"
        else:
            relax_dir = ""

        result_dir = os.path.join(organism_result_dir, solver, relax_dir)

        # if not os.path.exists(result_dir):
        #     os.makedirs(result_dir)
        # # write test results in files
        # file_path = os.path.join(result_dir, "sv.csv")
        # with open(file_path, 'w', encoding="utf-8") as fp:
        #     fp.write(sv.to_csv())
        # file_path = os.path.join(result_dir, "flux.csv")
        # with open(file_path, 'w', encoding="utf-8") as fp:
        #     fp.write(fluxes.to_csv())

        table = fluxes.to_numpy()
        table = numpy.array(table, dtype=float)

        file_path = os.path.join(result_dir, "flux.csv")
        expected_table = pandas.read_csv(file_path, index_col=0, header=0)
        print(expected_table)
        expected_table = expected_table.to_numpy()
        expected_table = numpy.array(expected_table, dtype=float)
        self.assertTrue(numpy.isclose(table, expected_table, rtol=1e-01).all())

        self.assertEqual(len(twin.networks), 1)

        for k in twin.networks:
            net = twin.networks[k]
            rxn = net.reactions["RB"]
            self.assertAlmostEqual(rxn.data["flux_estimates"]["values"][0], 0.374999, delta=1e-3)

            rxn = net.reactions["R1"]
            self.assertAlmostEqual(rxn.data["flux_estimates"]["values"][0], 29.99999, delta=1e-3)
