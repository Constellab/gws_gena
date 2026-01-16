import os

import numpy
import pandas
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, IExperiment
from gws_gena import ContextImporter, DataProvider, FBAProto, NetworkImporter


class TestFBA(BaseTestCaseUsingFullBiotaDB):
    def test_toy_fba(self):
        testdata_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(testdata_dir, "toy")
        organism_result_dir = os.path.join(testdata_dir, "fba", "toy")

        def run_fba(context, solver="highs", relax_qssa=False, parsimony_strength=0.0):
            experiment = IExperiment(FBAProto)
            proto = experiment.get_protocol()
            net = NetworkImporter.call(
                File(path=os.path.join(data_dir, "toy.json")), params={"add_biomass": True}
            )
            ctx = ContextImporter.call(
                File(
                    path=os.path.join(
                        data_dir, ("toy_context.json" if context else "toy_context_empty.json")
                    )
                )
            )

            proto.set_input("network", net)
            proto.set_input("context", ctx)
            fba = proto.get_process("fba")
            fba.set_param("solver", solver)
            fba.set_param("relax_qssa", relax_qssa)
            fba.set_param("parsimony_strength", parsimony_strength)
            experiment.run()

            # test results
            result = proto.get_output("fba_result")
            fluxes = result.get_fluxes_dataframe()
            sv = result.get_sv_dataframe()

            self.print(fluxes)
            self.print(sv)
            th, p = result.compute_zero_flux_threshold()
            self.print(
                f"sv_mean = {sv['value'].mean()}, sv_std = {sv['value'].std()}, sv_th={th}, sv_p = {p}"
            )

            relax_dir = ("relax" if relax_qssa else "no-relax") if solver == "quad" else ""

            if context:
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
                self.print(expected_table)
                expected_table = expected_table.to_numpy()
                expected_table = numpy.array(expected_table, dtype=float)
                self.assertTrue(numpy.isclose(table, expected_table, rtol=1e-01).all())

            # # export annotated network
            # annotated_twin = proto.get_output("twin")
            # net = list(annotated_twin.networks.values())[0]
            # with open(os.path.join(result_dir, './toy_fba_dump.json'), 'w', encoding="utf-8") as fp:
            #     data = net.dumps()
            #     json.dump(data, fp, indent=4)

        # highs
        for context in [True]:
            self.print(f"Test FBAProto: Small network (toy + context={context} + linprog)")
            run_fba(context=context, solver="highs")

        # quad
        for relax in [False, True]:
            self.print(f"Test FBAProto: Small network (toy + context + quad + relax={relax})")
            if relax:
                run_fba(context=True, solver="quad", relax_qssa=relax, parsimony_strength=1.0)
            else:
                run_fba(context=True, solver="quad", relax_qssa=relax)
