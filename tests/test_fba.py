import os, json
import pandas
import numpy

from gws_core import Settings, GTest, IExperiment, ExperimentService, File
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_gena import Network
from gws_gena import Twin, TwinContext
from gws_gena import FBA, FBAResult
from gws_gena.proto import FBAProto

settings = Settings.retrieve()

class TestFba(BaseTestCaseUsingFullBiotaDB):

    async def test_toy_fba(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")

        async def run_fba(context, solver="highs", relax_qssa=False):
            experiment = IExperiment(FBAProto)
            proto = experiment.get_protocol()

            network_file = File()
            network_file.path = os.path.join(data_dir, "toy.json")
            ctx_file = File()
            ctx_file.path = os.path.join(data_dir, ("toy_context.json" if context else "toy_context_empty.json"))

            proto.set_input("network_file", network_file)
            proto.set_input("context_file", ctx_file)

            fba = proto.get_process("fba")
            fba.set_param("solver", solver)

            await experiment.run()
    
            # test results
            result = proto.get_output("fba_result")
            fluxes = result.get_fluxes_as_table()
            sv = result.get_sv_as_table()
            print(fluxes)
            print(sv)
            th, p = result.compute_zero_flux_threshold()
            print(f"sv_mean = {sv.mean()}, sv_std = {sv.std()}, sv_th={th}, sv_p = {p}")

            if solver == "quad":
                relax_dir = "relax" if relax_qssa else "no-relax"
            else:
                relax_dir = ""

            if context:
                result_dir = os.path.join(data_dir, 'fba', solver, relax_dir)
                if not os.path.exists(result_dir):
                    os.makedirs(result_dir)
                # #write test results in files
                # file_path = os.path.join(result_dir,"sv.csv")
                # with open(file_path, 'w') as fp:
                #     fp.write(sv.to_csv())
                # file_path = os.path.join(result_dir,"flux.csv")
                # with open(file_path, 'w') as fp:
                #     fp.write(fluxes.to_csv())
                
                table = fluxes.to_numpy()
                file_path = os.path.join(result_dir,"flux.csv")
                expected_table = pandas.read_csv(file_path, index_col=0, header=0).to_numpy()
                table = numpy.array(table, dtype=float)
                expected_table = numpy.array(expected_table, dtype=float)
                self.assertTrue( numpy.isclose(table,expected_table,rtol=1e-02).all() )
            
            bio = proto.get_output("annotated_twin")
            net = list(bio.networks.values())[0]
            tflux = net.get_total_abs_flux_as_table()
            print(tflux)

            tflux2 = result.get_total_abs_flux_as_table()
            print("----")
            print(tflux2)
            self.assertTrue( tflux.equals(tflux2) )

            bio = result.get_related_twin()
            self.assertIsInstance( bio, Twin )

        # highs
        for context in [False, True]:
            self.print(f"Test FBAProto: Small network (toy + context={context} + linprog)")
            await run_fba(context=context,solver="highs")
        # quad
        for relax in [False, True]:
            self.print(f"Test FBAProto: Small network (toy + context + quad + relax={relax})")
            await run_fba(context=True,solver="quad",relax_qssa=relax) 

    async def test_large_fba(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        
        async def run_fba(organism, solver="highs", relax_qssa=False):
            experiment = IExperiment(FBAProto)
            proto = experiment.get_protocol()

            organism_dir = os.path.join(data_dir, organism)
            network_file = File()
            network_file.path = os.path.join(organism_dir, f"{organism}.json")
            ctx_file = File()
            ctx_file.path = os.path.join(organism_dir, f"{organism}_context.json")

            proto.set_input("network_file", network_file)
            proto.set_input("context_file", ctx_file)
            fba = proto.get_process("fba")
            fba.set_param('solver', solver)
            fba.set_param('relax_qssa', relax_qssa)
            if organism == 'ecoli':
                fba.set_param('fluxes_to_maximize', ["ecoli_BIOMASS_Ecoli_core_w_GAM:1.0"])
            else:
                fba.set_param('fluxes_to_maximize', ["pcys_Biomass:1.0"])

            await experiment.run()
            
            relax_dir = ""
            if solver == "quad":
                relax_dir = "relax" if relax_qssa else "no-relax"

            # test results
            result = proto.get_output("fba_result")
            fluxes = result.get_fluxes_as_table()
            if organism == 'ecoli':
                biomass_flux = fluxes.loc[["ecoli_BIOMASS_Ecoli_core_w_GAM"],:]
            else:
                biomass_flux = fluxes.loc[["pcys_Biomass"],:]

            sv = result.get_sv_as_table()
            print(fluxes)
            print(sv)
            print(biomass_flux)
            th, p = result.compute_zero_flux_threshold()
            print(f"sv_mean = {sv.mean()}, sv_std = {sv.std()}, sv_th={th}, sv_p = {p}")

            result_dir = os.path.join(organism_dir, 'fba', solver, relax_dir)
            # if not os.path.exists(result_dir):
            #     os.makedirs(result_dir)
            # file_path = os.path.join(result_dir,"flux.csv")
            # with open(file_path, 'w') as fp:
            #     fp.write( fluxes.to_csv() )
            # file_path = os.path.join(result_dir,"sv.csv")
            # with open(file_path, 'w') as fp:
            #     fp.write( sv.to_csv() )
            # file_path = os.path.join(result_dir,"biomass_flux.csv")
            # with open(file_path, 'w') as fp:
            #     fp.write( biomass_flux.to_csv() )

            table = fluxes.to_numpy()
            file_path = os.path.join(result_dir,"flux.csv")
            expected_table = pandas.read_csv(file_path, index_col=0, header=0).to_numpy()
            table = numpy.array(table, dtype=float)
            expected_table = numpy.array(expected_table, dtype=float)
            self.assertTrue( numpy.isclose(table,expected_table,rtol=1e-01).all() )

            bio = proto.get_output("annotated_twin")
            net = list(bio.networks.values())[0]
            tflux = net.get_total_abs_flux_as_table()
            print(tflux)

            tflux2 = result.get_total_abs_flux_as_table()
            print("----")
            print(tflux2)
            self.assertTrue( tflux.equals(tflux2) )

            bio = result.get_related_twin()
            self.assertIsInstance( bio, Twin )
            #bio_json = result.get_annotated_twin_as_json()
            #print(bio_json)

        # ecoli
        organism = "ecoli"
        self.print(f"Test FBAProto: Medium- or large-size network ({organism} + linprog)")
        await run_fba(organism=organism, solver="highs")
        for relax in [False, True]:
            self.print(f"Test FBAProto: Medium- or large-size network ({organism} + quad)")
            await run_fba(organism=organism, solver="quad", relax_qssa=relax)
        
        # pcys
        for relax in [True]:
            organism = "pcys"
            self.print(f"Test FBAProto: Medium- or large-size network ({organism} + quad)")
            await run_fba(organism=organism, solver="quad", relax_qssa=True)