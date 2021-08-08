
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
from gena.deprec.fba.fba import FBA, FBAResult
from gena.deprec.fba.proto.fba_proto import FBAProto

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

    def test_fba(self):
        GTest.print("Test FBAProto")
        data_dir = settings.get_dir("gena:testdata_dir")

        def run_fba( organism, number_of_randomizations=1 ):
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
            fba.set_param("number_of_randomizations", number_of_randomizations)
            fba.set_param("use_hard_bounds", True)
            fba.set_param("verbose", False)

            def _on_end(*args, **kwargs):
                result = proto.output["fba_result"]
                result_dir = os.path.join(organism_dir, 'fba_deprec', f'nrnd={number_of_randomizations}')
                if not os.path.exists(result_dir):
                    os.makedirs(result_dir)

                fluxes = result.render__flux_ranges__as_table()
                sv = result.render__sv_ranges__as_table()
                print(fluxes)
                print(sv)

                # file_path = os.path.join(result_dir,"flux.csv")
                # with open(file_path, 'w') as fp:
                #     fp.write( fluxes.to_csv() )
                # file_path = os.path.join(result_dir,"sv.csv")
                # with open(file_path, 'w') as fp:
                #     fp.write( sv.to_csv() )

                if organism == "ecoli":
                    biomass_flux = fluxes.loc[["ecoli_BIOMASS_Ecoli_core_w_GAM"],:]
                    file_path = os.path.join(result_dir,"biomass_flux.csv")
                    with open(file_path, 'w') as fp:
                        fp.write( biomass_flux.to_csv() )

                    print(biomass_flux)

                table = fluxes.to_numpy()
                table = numpy.array(table, dtype=float)
                file_path = os.path.join(result_dir,"flux.csv")
                expected_table = pandas.read_csv(file_path, index_col=0, header=0).to_numpy()
                expected_table = numpy.array(expected_table, dtype=float)
                self.assertTrue( numpy.isclose(table,expected_table,rtol=1e-01,equal_nan=True).all() )

            e = proto.create_experiment(study=GTest.study, user=GTest.user)
            e.on_end(_on_end)
            asyncio.run( e.run() )
        
        run_fba( organism="toy", number_of_randomizations=1  )
        run_fba( organism="toy", number_of_randomizations=100 )
        run_fba( organism="ecoli", number_of_randomizations=100 )

        