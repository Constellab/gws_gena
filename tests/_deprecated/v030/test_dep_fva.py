import json
import os

import numpy
import pandas
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ExperimentService, File, GTest, IExperiment, Settings
from gws_gena import (Network, NetworkImporter, Twin, Context,
                      ContextImporter)
from gws_gena.deprecated.v030.dep_fva_proto import FVAProto

settings = Settings.retrieve()


class TestFba(BaseTestCaseUsingFullBiotaDB):

    async def test_small_fva(self):
        self.print("Test FVAProto: Small metwork")
        testdata_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(testdata_dir, "toy")
        organism_result_dir = os.path.join(testdata_dir, 'fva', "toy")

        async def run_fva(solver="highs", relax_qssa=False):
            experiment = IExperiment(FVAProto)
            proto = experiment.get_protocol()

            network_file = File()
            network_file.path = os.path.join(data_dir, "toy.json")
            ctx_file = File()
            ctx_file.path = os.path.join(data_dir, "toy_context.json")

            net = NetworkImporter.call(File(
                path=os.path.join(data_dir, "toy.json")
            ))
            ctx = ContextImporter.call(File(
                path=os.path.join(data_dir, "toy_context.json")
            ))

            proto.set_input("network", net)
            proto.set_input("context", ctx)

            fva = proto.get_process("fva")
            fva.set_param("solver", solver)
            fva.set_param("relax_qssa", relax_qssa)

            await experiment.run()

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
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)

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
            expected_table = expected_table.to_numpy()
            expected_table = numpy.array(expected_table, dtype=float)

            self.assertTrue(numpy.isclose(table, expected_table, rtol=1e-01).all())

        GTest.print(f"Test FVAProto: Small network (toy + linprog)")
        await run_fva(solver="highs")

        for relax_qssa in [True, False]:
            GTest.print(f"Test FVAProto: Small network (toy + quad + relax={relax_qssa})")
            await run_fva(solver="quad", relax_qssa=False)

    async def test_large_fba(self):
        self.print("Test FBAProto: Medium or large metwork (typically Ecoli)")
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        async def run_fva(organism, solver="highs", relax_qssa=False):
            experiment = IExperiment(FVAProto)
            proto = experiment.get_protocol()

            organism_dir = os.path.join(data_dir, organism)
            organism_result_dir = os.path.join(data_dir, 'fva', organism)

            net = NetworkImporter.call(
                File(path=os.path.join(organism_dir, f"{organism}.json")),
                {"skip_bigg_exchange_reactions": False}
            )
            ctx = ContextImporter.call(File(
                path=os.path.join(organism_dir, f"{organism}_context.json")
            ))

            proto.set_input("network", net)
            proto.set_input("context", ctx)

            fva = proto.get_process("fva")
            fva.set_param('solver', solver)
            fva.set_param('relax_qssa', relax_qssa)

            if organism == 'ecoli':
                fva.set_param('fluxes_to_maximize', ["ecoli_BIOMASS_Ecoli_core_w_GAM:1.0"])
            else:
                fva.set_param('fluxes_to_maximize', ["pcys_Biomass:1.0"])

            await experiment.run()

            relax_dir = ""
            if solver == "quad":
                relax_dir = "relax" if relax_qssa else "no-relax"

            # test results
            result = proto.get_output("fva_result")
            fluxes = result.get_fluxes_dataframe()
            sv = result.get_sv_dataframe()

            if organism == 'ecoli':
                biomass_flux = result.get_fluxes_by_reaction_ids(["ecoli_BIOMASS_Ecoli_core_w_GAM"])
            else:
                biomass_flux = result.get_fluxes_by_reaction_ids(["pcys_Biomass"])

            print(fluxes)
            print(sv)
            print(biomass_flux)
            th, p = result.compute_zero_flux_threshold()
            print(f"sv_mean = {sv['value'].mean()}, sv_std = {sv['value'].std()}, sv_th={th}, sv_p = {p}")

            result_dir = os.path.join(organism_result_dir, solver, relax_dir)
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)

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


        # ecoli
        organism = "ecoli"
        GTest.print(f"Test FBAProto: Medium- or large-size network ({organism} + linprog)")
        await run_fva(organism=organism, solver="highs")
        for relax in [True]:
            GTest.print(f"Test FBAProto: Medium- or large-size network ({organism} + quad)")
            await run_fva(organism=organism, solver="quad", relax_qssa=relax)

        # pcys
        organism = "pcys"
        GTest.print(f"Test FBAProto: Medium- or large-size network ({organism} + quad)")
        await run_fva(organism=organism, solver="quad", relax_qssa=True)
