import os

import numpy
import pandas
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, GTest, IExperiment, Settings
from gws_gena import ContextImporter, FVAProto, NetworkImporter

settings = Settings.get_instance()


class TestFVA(BaseTestCaseUsingFullBiotaDB):

    def test_toy_fva(self):
        self.print("Test FVAProto: Small metwork")
        testdata_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(testdata_dir, "toy")
        organism_result_dir = os.path.join(testdata_dir, 'fva', "toy")

        def run_fva(solver="highs", relax_qssa=False, parsimony_strength = 0.0):
            experiment = IExperiment(FVAProto)
            proto = experiment.get_protocol()

            network_file = File()
            network_file.path = os.path.join(data_dir, "toy.json")
            ctx_file = File()
            ctx_file.path = os.path.join(data_dir, "toy_context.json")

            net = NetworkImporter.call(File(
                path=os.path.join(data_dir, "toy.json")
            ),params = {"add_biomass" : True})
            ctx = ContextImporter.call(File(
                path=os.path.join(data_dir, "toy_context.json")
            ))

            proto.set_input("network", net)
            proto.set_input("context", ctx)

            fva = proto.get_process("fva")
            fva.set_param("solver", solver)
            fva.set_param("relax_qssa", relax_qssa)

            experiment.run()

            relax_dir = ""
            if solver == "quad":
                relax_dir = "relax" if relax_qssa else "no-relax"

            # test results
            result = proto.get_output("fva_result")
            fluxes = result.get_fluxes_dataframe()
            sv = result.get_sv_dataframe()
            print(fluxes)
            print(sv)
            th, p = result.compute_zero_flux_threshold()
            print(f"sv_mean = {sv['value'].mean()}, sv_std = {sv['value'].std()}, sv_th={th}, sv_p = {p}")

            result_dir = os.path.join(organism_result_dir, solver, relax_dir)

            # if not os.path.exists(result_dir):
            #     os.makedirs(result_dir)
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
            expected_table = expected_table.to_numpy()
            expected_table = numpy.array(expected_table, dtype=float)

            self.assertTrue(numpy.isclose(table, expected_table, rtol=1e-01).all())

            # # export annotated network
            # annotated_twin = proto.get_output("twin")
            # net = list(annotated_twin.networks.values())[0]
            # with open(os.path.join(result_dir, './toy_fva_dump.json'), 'w', encoding="utf-8") as fp:
            #     data = net.dumps()
            #     json.dump(data, fp, indent=4)



        GTest.print("Test FVAProto: Small network (toy + linprog)")
        run_fva(solver="highs")

        for relax_qssa in [True, False]:
            GTest.print(f"Test FVAProto: Small network (toy + quad + relax={relax_qssa})")
            run_fva(solver="quad", relax_qssa=relax_qssa)
