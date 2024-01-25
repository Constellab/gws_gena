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

        def run_fba(organism, solver="highs", relax_qssa=False, translate_ids=False):
            experiment = IExperiment(FBAProto)
            proto = experiment.get_protocol()
            organism_dir = os.path.join(data_dir, organism)
            organism_result_dir = os.path.join(data_dir, 'fba', organism)
            net = NetworkImporter.call(
                File(os.path.join(organism_dir, f"{organism}.json")),
                params={"translate_ids": translate_ids}
            )
            ctx = ContextImporter.call(File(
                os.path.join(organism_dir, f"{organism}_context.json")
            ))

            proto.set_input("network", net)
            proto.set_input("context", ctx)
            fba = proto.get_process("fba")
            fba.set_param('solver', solver)
            fba.set_param('relax_qssa', relax_qssa)
            fba.set_param('qssa_relaxation_strength', 1)
            if organism == 'ecoli':
                # fba.set_param('fluxes_to_maximize', ["ecoli_BIOMASS_Ecoli_core_w_GAM:1.0"])
                fba.set_param('biomass_optimization', "maximize")
            else:
                fba.set_param('fluxes_to_maximize', ["pcys_Biomass:1.0"])

            experiment.run()

            relax_dir = ""
            if solver == "quad":
                relax_dir = "relax" if relax_qssa else "no-relax"

            # test results
            result = proto.get_output("fba_result")
            #biomass_flux = result.get_biomass_flux_dataframe()
            #print("---------------- BIOMASS FLUX ----------------")
            #print(biomass_flux)
            #print("----------------------------------------------")

            result_dir = os.path.join(organism_result_dir, solver, relax_dir)
            file_path = os.path.join(result_dir, "biomass_flux.csv")
            # with open(file_path, 'w', encoding="utf-8") as fp:
            #     fp.write(biomass_flux.to_csv())
            #biomass_flux = biomass_flux.to_numpy()
            expected_biomass_flux = pandas.read_csv(file_path, index_col=0, header=0)
            expected_biomass_flux = expected_biomass_flux.to_numpy()
            #self.assertTrue(numpy.isclose(biomass_flux, expected_biomass_flux, rtol=1e-02).all())

            fluxes = result.get_fluxes_dataframe()
            print(fluxes)
            print(fluxes.abs().sum())
            sv = result.get_sv_dataframe()
            th, p = result.compute_zero_flux_threshold()
            print(f"sv_mean = {sv['value'].mean()}, sv_std = {sv['value'].std()}, sv_th={th}, sv_p = {p}")

            # if not os.path.exists(result_dir):
            #     os.makedirs(result_dir)
            # file_path = os.path.join(result_dir, "flux.csv")
            # with open(file_path, 'w', encoding="utf-8") as fp:
            #     fp.write(fluxes.to_csv())
            # file_path = os.path.join(result_dir, "sv.csv")
            # with open(file_path, 'w', encoding="utf-8") as fp:
            #     fp.write(sv.to_csv())
            
            table = fluxes.to_numpy()
            table = numpy.array(table, dtype=float)
            file_path = os.path.join(result_dir, "flux.csv")
            expected_table = pandas.read_csv(file_path, index_col=0, header=0)
            expected_table = expected_table.to_numpy()
            expected_table = numpy.array(expected_table, dtype=float)
            self.assertTrue(numpy.isclose(table, expected_table, rtol=1e-01).all())

        organism = "ecoli"
        self.print(f"Test FBAProto: Medium- or large-size network ({organism} + linprog)")
        run_fba(organism=organism, solver="highs")

        for relax in [False, True]:
            self.print(f"Test FBAProto: Medium- or large-size network ({organism} + quad)")
            run_fba(organism=organism, solver="quad", relax_qssa=relax)

        # for relax in [True]:
        #     self.print(f"Test FBAProto: Medium- or large-size network ({organism} + quad + translate ids)")
        #     run_fba(organism=organism, solver="quad", relax_qssa=relax, translate_ids=True)
