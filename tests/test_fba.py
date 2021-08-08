
import asyncio
import os, json
import unittest
import pandas
import numpy

from gws.settings import Settings
from gws.file import File
from gws.unittest import GTest

settings = Settings.retrieve()

from gena import Network
from gena import BioModel, Context
from gena import FBA, FBAResult
from gena.proto import FBAProto

from biota.base import DbManager as BiotaDbManager

class TestFba(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()
        BiotaDbManager.use_prod_db(True)

    @classmethod
    def tearDownClass(cls):
        BiotaDbManager.use_prod_db(False)
        GTest.drop_tables()

    def test_toy_fba(self):
        data_dir = settings.get_dir("gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")
        def run_fba(context, solver="highs", relax_qssa=False):
            proto = FBAProto()
            file_path = os.path.join(data_dir, "toy.json")
            try:
                network_file = File.get(File.path == file_path)
            except:
                network_file = File(path=file_path)
            if context:
                file_path = os.path.join(data_dir, "toy_context.json")
            else:
                file_path = os.path.join(data_dir, "toy_context_empty.json")
            try:
                ctx_file = File.get(File.path == file_path)
            except:
                ctx_file = File(path=file_path)

            proto.input["network_file"] = network_file
            proto.input["context_file"] = ctx_file
            fba = proto.get_fba()
            fba.set_param("solver", solver)

            relax_dir = ""
            if solver == "quad":
                relax_dir = "relax" if relax_qssa else "no-relax"

            def _on_end(*args, **kwargs):
                result = proto.output["fba_result"]
                fluxes = result.render__fluxes__as_table()
                sv = result.render__sv__as_table()
                print(fluxes)
                print(sv)
                th, p = result.compute_zero_flux_threshold()
                print(f"sv_mean = {sv.mean()}, sv_std = {sv.std()}, sv_th={th}, sv_p = {p}")

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
                
                bio = proto.output["annotated_biomodel"]
                net = list(bio.networks.values())[0]
                tflux = net.render__total_abs_flux__as_table()
                print(tflux)

                tflux2 = result.render__total_abs_flux__as_table()
                print("----")
                print(tflux2)
                self.assertTrue( tflux.equals(tflux2) )

                bio = result.get_related_model(relation_name="biomodel")
                self.assertIsInstance( bio, BioModel )

            e = proto.create_experiment(study=GTest.study, user=GTest.user)
            e.on_end(_on_end)
            asyncio.run( e.run() )

        # highs
        for context in [False, True]:
            GTest.print(f"Test FBAProto: Small network (toy + context={context} + linprog)")
            run_fba(context=context,solver="highs")
        # quad
        for relax in [False, True]:
            GTest.print(f"Test FBAProto: Small network (toy + context + quad + relax={relax})")
            run_fba(context=True,solver="quad",relax_qssa=relax) 

    def test_large_fba(self):
        data_dir = settings.get_dir("gena:testdata_dir")
        def run_fba(organism, solver="highs", relax_qssa=False):
            proto = FBAProto()
            organism_dir = os.path.join(data_dir, organism)
            file_path = os.path.join(organism_dir, f"{organism}.json")
            try:
                network_file = File.get(File.path == file_path)
            except:
                network_file = File(path=file_path)                
            file_path = os.path.join(organism_dir, f"{organism}_context.json")
            try:
                ctx_file = File.get(File.path == file_path)
            except:
                ctx_file = File(path=file_path)

            proto.input["network_file"] = network_file
            proto.input["context_file"] = ctx_file
            fba = proto.get_fba()
            fba.set_param('solver', solver)
            fba.set_param('relax_qssa', relax_qssa)
            if organism == 'ecoli':
                fba.set_param('fluxes_to_maximize', ["ecoli_BIOMASS_Ecoli_core_w_GAM:1.0"])
            else:
                fba.set_param('fluxes_to_maximize', ["pcys_Biomass:1.0"])

            relax_dir = ""
            if solver == "quad":
                relax_dir = "relax" if relax_qssa else "no-relax"

            def _on_end(*args, **kwargs):
                result = proto.output["fba_result"]
                fluxes = result.render__fluxes__as_table()
                if organism == 'ecoli':
                    biomass_flux = fluxes.loc[["ecoli_BIOMASS_Ecoli_core_w_GAM"],:]
                else:
                    biomass_flux = fluxes.loc[["pcys_Biomass"],:]

                sv = result.render__sv__as_table()
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

                bio = proto.output["annotated_biomodel"]
                net = list(bio.networks.values())[0]
                tflux = net.render__total_abs_flux__as_table()
                print(tflux)

                tflux2 = result.render__total_abs_flux__as_table()
                print("----")
                print(tflux2)
                self.assertTrue( tflux.equals(tflux2) )

                bio = result.get_related_model(relation_name="biomodel")
                self.assertIsInstance( bio, BioModel )
                #bio_json = result.render__annotated_biomodel__as_json()
                #print(bio_json)

            e = proto.create_experiment(study=GTest.study, user=GTest.user)
            e.on_end(_on_end)
            asyncio.run( e.run() )

        # ecoli
        organism = "ecoli"
        GTest.print(f"Test FBAProto: Medium- or large-size network ({organism} + linprog)")
        run_fba(organism=organism, solver="highs")
        for relax in [False, True]:
            GTest.print(f"Test FBAProto: Medium- or large-size network ({organism} + quad)")
            run_fba(organism=organism, solver="quad", relax_qssa=relax)
        # pcys
        for relax in [True]:
            organism = "pcys"
            GTest.print(f"Test FBAProto: Medium- or large-size network ({organism} + quad)")
            run_fba(organism=organism, solver="quad", relax_qssa=True)