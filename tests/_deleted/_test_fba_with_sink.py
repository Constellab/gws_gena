import json
import os

import numpy
import pandas
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ExperimentService, File, GTest, IExperiment, Settings
from gws_gena import (FBAProto, Network, NetworkImporter, Twin, Context,
                      ContextImporter)

settings = Settings.retrieve()


class TestFba(BaseTestCaseUsingFullBiotaDB):

    async def test_toy_fba(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy_with_gap")

        async def run_fba(context, solver="highs", fill_gaps_with_sinks=True, relax_steady_state=False):
            experiment = IExperiment(FBAProto)
            proto = experiment.get_protocol()

            net = NetworkImporter.call(File(
                path=os.path.join(data_dir, "toy_network.json"))
            )
            ctx = ContextImporter.call(
                File(path=os.path.join(data_dir, "toy_context.json"))
            )

            proto.set_input("network", net)
            proto.set_input("context", ctx)
            fba = proto.get_process("fba")
            fba.set_param("solver", solver)
            fba.set_param("fill_gaps_with_sinks", fill_gaps_with_sinks)
            fba.set_param("relax_qssa", relax_steady_state)

            await experiment.run()

            # test results
            result = proto.get_output("fba_result")
            fluxes = result.get_fluxes_dataframe()
            sv = result.get_sv_dataframe()
            print(fluxes)
            print(sv)

            fill_dir = "sink" if fill_gaps_with_sinks else "no_sink"
            relax_dir = "relax" if relax_steady_state else "no_relax"

            if context:
                result_dir = os.path.join(data_dir, 'fba', solver, fill_dir, relax_dir)
                if not os.path.exists(result_dir):
                    os.makedirs(result_dir)
                # write test results in files
                file_path = os.path.join(result_dir, "sv.csv")
                with open(file_path, 'w') as fp:
                    fp.write(sv.to_csv())
                file_path = os.path.join(result_dir, "flux.csv")
                with open(file_path, 'w') as fp:
                    fp.write(fluxes.to_csv())

                table = fluxes.to_numpy()
                file_path = os.path.join(result_dir, "flux.csv")
                expected_table = pandas.read_csv(file_path, index_col=0, header=0).to_numpy()
                table = numpy.array(table, dtype=float)
                expected_table = numpy.array(expected_table, dtype=float)
                #self.assertTrue( numpy.isclose(table,expected_table,rtol=1e-02).all() )

            bio = proto.get_output("annotated_twin")
            net = list(bio.networks.values())[0]
            tflux = net.get_total_abs_flux_as_table()
            print(tflux)

        # fill_with_sink = True, relax = False
        self.print("Test FBAProto: Small network (toy + context + linprog)")
        await run_fba(context=True, solver="highs", fill_gaps_with_sinks=True)
        self.print("Test FBAProto: Small network (toy + context + quad)")
        await run_fba(context=True, solver="quad", fill_gaps_with_sinks=True)

        # fill_with_sink = False, relax = True
        self.print("Test FBAProto: Small network (toy + context + quad)")
        await run_fba(context=True, solver="quad", fill_gaps_with_sinks=False, relax_steady_state=True)