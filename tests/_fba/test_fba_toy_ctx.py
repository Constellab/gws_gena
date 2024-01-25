import os

import numpy
import pandas
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, IExperiment, Settings, TaskRunner
from gws_gena import (ContextBuilder, FBAProto, FluxTableImporter,
                      NetworkImporter)

settings = Settings.get_instance()


class TestFBA(BaseTestCaseUsingFullBiotaDB):

    def test_toy_fba_with_context_builder(self):
        testdata_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(testdata_dir, "toy")
        organism_result_dir = os.path.join(testdata_dir, 'fba', "toy_ctx")

        def run_fba(ctx_name, solver="highs", relax_qssa=False, parsimony_strength = 0.0):
            file_path = os.path.join(data_dir, "ctx_data", f"{ctx_name}.csv")
            flux_data = FluxTableImporter.call(File(path=file_path), params={"delimiter": ","})
            net = NetworkImporter.call(File(path=os.path.join(data_dir, "toy.json")), params={})

            # build context
            tester = TaskRunner(
                inputs={"network": net, "flux_table": flux_data},
                task_type=ContextBuilder
            )
            output = tester.run()
            ctx = output["context"]

            # run fba
            experiment = IExperiment(FBAProto)
            proto = experiment.get_protocol()
            proto.set_input("network", net)
            proto.set_input("context", ctx)
            fba = proto.get_process("fba")
            fba.set_param("solver", solver)
            fba.set_param('fluxes_to_maximize', ["toy_cell_RB"])
            experiment.run()

            # test results
            result = proto.get_output("fba_result")
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

            result_dir = os.path.join(organism_result_dir, ctx_name, solver, relax_dir)

            #if not os.path.exists(result_dir):
            #    os.makedirs(result_dir)
            # # write test results in files
            # file_path = os.path.join(result_dir, "sv.csv")
            # with open(file_path, 'w', encoding="utf-8") as fp:
            #     fp.write(sv.to_csv())
            # file_path = os.path.join(result_dir, "flux.csv")
            # with open(file_path, 'w', encoding="utf-8") as fp:
            #     fp.write(fluxes.to_csv())

            print(fluxes)
            table = fluxes.to_numpy()
            table = numpy.array(table, dtype=float)

            file_path = os.path.join(result_dir, "flux.csv")
            expected_table = pandas.read_csv(file_path, index_col=0, header=0)
            expected_table = expected_table.to_numpy()
            expected_table = numpy.array(expected_table, dtype=float)
            self.assertTrue(numpy.isclose(table, expected_table, rtol=1e-01).all())

        # quad
        relax = True
        self.print(f"Test FBAProto: Small network (toy + context + quad + relax={relax})")

        for i in range(1, 6):
            ctx_name = f"toy_ctx_data_{i}"
            run_fba(ctx_name=ctx_name, solver="quad", relax_qssa=relax)
