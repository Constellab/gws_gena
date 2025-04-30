import os

import numpy
import pandas
from gws_core import File, Settings, TaskRunner, BaseTestCase
from gws_gena import ContextImporter
from gws_gena.fva.fva_result import FVAResult
from gws_gena.fva.fva_v2 import FVAV2
from gws_gena.network.network_task.network_importer_v2 import NetworkImporterV2
from gws_gena.twin.twin_v2 import TwinV2


settings = Settings.get_instance()


class TestFVA(BaseTestCase):

    def test_toy_fva(self):
        self.print("Test FVAProto: Small network")
        testdata_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(testdata_dir, "toy")
        organism_result_dir = os.path.join(testdata_dir, 'fva', "toy")

        def run_fva(solver="highs", relax_qssa=False):
            net = NetworkImporterV2.call(File(
            path=os.path.join(data_dir, "toy.json"))
            )
            ctx = ContextImporter.call(
                File(path=os.path.join(
                    data_dir, ("toy_context.json"))
            ))

            # build the twin
            twin = TwinV2()
            twin.set_network(net)
            twin.set_context(ctx)

            task_runner = TaskRunner(FVAV2,
                                 inputs={
                                     "twin": twin
                                 },
                                 params={
                                    "solver": solver,
                                    "relax_qssa": relax_qssa,
                                    "add_biomass": True
                                 })

            task_runner.run()

            relax_dir = ""
            if solver == "quad":
                relax_dir = "relax" if relax_qssa else "no-relax"

            # test results
            result: FVAResult = task_runner.get_output("fva_result")
            fluxes = result.get_fluxes_dataframe()

            sv = result.get_sv_dataframe()

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

        run_fva(solver="highs")

        for relax_qssa in [True, False]:
            run_fva(solver="quad", relax_qssa=relax_qssa)
