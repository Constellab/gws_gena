import os

import numpy
import pandas
from gws_core import BaseTestCase, File, Settings, TaskRunner
from gws_gena import ContextImporter
from gws_gena.fba.fba_result import FBAResult
from gws_gena.network_v2.fba_v2 import FBAV2
from gws_gena.network_v2.network_importer_v2 import NetworkImporterV2
from gws_gena.network_v2.twin_v2 import TwinV2


# gws_gena/test_fba_toy_v2
class TestFBA(BaseTestCase):

    def test_toy_fba(self):
        settings = Settings.get_instance()
        testdata_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(testdata_dir, "toy")
        organism_result_dir = os.path.join(testdata_dir, 'fba', "toy")

        # highs
        for context in [True]:
            self.print(
                f"Test FBAProto: Small network (toy + context={context} + linprog)")
            self._run_fba(context=context, data_dir=data_dir, organism_result_dir=organism_result_dir,
                          solver="highs")

        # quad
        for relax in [False, True]:
            self.print(
                f"Test FBAProto: Small network (toy + context + quad + relax={relax})")
            if relax:
                self._run_fba(context=True, data_dir=data_dir, organism_result_dir=organism_result_dir,
                              solver="quad", relax_qssa=relax, parsimony_strength=1.0)
            else:
                self._run_fba(context=True, data_dir=data_dir,
                              organism_result_dir=organism_result_dir, solver="quad", relax_qssa=relax)

    def _run_fba(self, context, data_dir: str, organism_result_dir: str,
                 solver="highs", relax_qssa=False, parsimony_strength=0.0):

        net = NetworkImporterV2.call(File(
            path=os.path.join(data_dir, "toy.json")),
            params={"add_biomass": True}
        )
        ctx = ContextImporter.call(
            File(path=os.path.join(
                data_dir, ("toy_context.json" if context else "toy_context_empty.json")))
        )

        # build the twin
        twin = TwinV2()
        twin.set_network(net)
        twin.set_context(ctx)

        task_runner = TaskRunner(FBAV2,
                                 inputs={
                                     "twin": twin
                                 },
                                 params={
                                     "solver": solver,
                                     "relax_qssa": relax_qssa,
                                     "parsimony_strength": parsimony_strength
                                 })

        task_runner.run()

        # test results
        result: FBAResult = task_runner.get_output("fba_result")
        fluxes = result.get_fluxes_dataframe()

        if solver == "quad":
            relax_dir = "relax" if relax_qssa else "no-relax"
        else:
            relax_dir = ""

        if context:
            result_dir = os.path.join(
                organism_result_dir, solver, relax_dir)

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
            expected_table = pandas.read_csv(
                file_path, index_col=0, header=0)
            expected_table = expected_table.to_numpy()
            expected_table = numpy.array(expected_table, dtype=float)
            self.assertTrue(numpy.isclose(
                table, expected_table, rtol=1e-01).all())

        # # export annotated network
        # annotated_twin = proto.get_output("twin")
        # net = list(annotated_twin.networks.values())[0]
        # with open(os.path.join(result_dir, './toy_fba_dump.json'), 'w', encoding="utf-8") as fp:
        #     data = net.dumps()
        #     json.dump(data, fp, indent=4)
