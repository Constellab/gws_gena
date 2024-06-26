import os

import numpy
import pandas
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, IExperiment, Settings
from gws_gena import ContextImporter, FBAProto, NetworkImporter

settings = Settings.get_instance()


class TestFBA(BaseTestCaseUsingFullBiotaDB):

    def test_large_fba(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        def run_fba(organism, solver="highs", relax_qssa=False):
            experiment = IExperiment(FBAProto)
            proto = experiment.get_protocol()
            organism_dir = os.path.join(data_dir, organism)
            organism_result_dir = os.path.join(data_dir, 'fba', organism)
            net = NetworkImporter.call(
                File(os.path.join(organism_dir, f"{organism}.json")),
                params= {"add_biomass" : True}
            )
            ctx = ContextImporter.call(File(
                os.path.join(organism_dir, f"{organism}_context_2simus.json")
            ))

            proto.set_input("network", net)
            proto.set_input("context", ctx)
            fba = proto.get_process("fba")
            fba.set_param('solver', solver)
            fba.set_param('relax_qssa', relax_qssa)
            fba.set_param('qssa_relaxation_strength', 1)
            if organism == 'ecoli':
                fba.set_param('biomass_optimization', "maximize")
            else:
                fba.set_param('fluxes_to_maximize', ["pcys_Biomass:1.0"])

            experiment.run()

            relax_dir = ""
            if solver == "quad":
                relax_dir = "relax" if relax_qssa else "no-relax"

            # test results
            result = proto.get_output("fba_result")


            fluxes = result.get_fluxes_dataframe()
            print(fluxes)
            print(fluxes.abs().sum())
            sv = result.get_sv_dataframe()
            th, p = result.compute_zero_flux_threshold()
            print(f"sv_mean = {sv['value'].mean()}, sv_std = {sv['value'].std()}, sv_th={th}, sv_p = {p}")

        # pcys
        for relax in [True]:
            organism = "pcys"
            self.print(f"Test FBAProto: Medium- or large-size network ({organism} + quad)")
            run_fba(organism=organism, solver="quad", relax_qssa=relax)
