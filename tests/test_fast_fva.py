
import asyncio
import os, json
import unittest
import pandas
import numpy

from gws.settings import Settings
from gws.file import File
from gws.unittest import GTest

settings = Settings.retrieve()

from gena.network import Network
from gena.context import Context
from gena.biomodel import BioModel
from gena.fast_fva import FastFVA, FastFVAResult
from gena.fast_fva_proto import FastFVAProto

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

    def test_small_fva(self):
        GTest.print("Test FastFVAProto: Small metwork")
        data_dir = settings.get_dir("gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")
        
        proto = FastFVAProto()
        file_path = os.path.join(data_dir, "toy_network.json")
        network_file = File(path=file_path)
        file_path = os.path.join(data_dir, "toy_context.json")
        ctx_file = File(path=file_path)

        proto.input["network_file"] = network_file
        proto.input["context_file"] = ctx_file

        fva = proto.get_fva()

        def _on_end(*args, **kwargs):
            result = proto.output["fva_result"]
            print(result.render__fluxes__as_table())
            print(result.render__sv__as_table())
   
        e = proto.create_experiment(study=GTest.study, user=GTest.user)
        e.on_end(_on_end)
        asyncio.run( e.run() )


    def test_large_fba(self):
        GTest.print("Test FBAProto: Medium or large metwork (typically Ecoli)")
        data_dir = settings.get_dir("gena:testdata_dir")

        proto = FastFVAProto()
        organism = 'ecoli'

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
        fba = proto.get_fva()

        if organism == 'ecoli':
            fba.set_param('fluxes_to_maximize', ["ecoli_BIOMASS_Ecoli_core_w_GAM:1.0"])
        else:
            fba.set_param('fluxes_to_maximize', ["pcys_Biomass:1.0"])

        def _on_end(*args, **kwargs):
            result = proto.output["fva_result"]
            fluxes = result.render__fluxes__as_table()
            sv = result.render__sv__as_table()
            print(fluxes)
            print(sv)

            result_dir = os.path.join(organism_dir, 'fast_fva')
            # if not os.path.exists(result_dir):
            #     os.makedirs(result_dir)
            
            # file_path = os.path.join(result_dir,"flux.csv")
            # with open(file_path, 'w') as fp:
            #     fp.write( fluxes.to_csv() )
            
            # file_path = os.path.join(result_dir,"sv.csv")
            # with open(file_path, 'w') as fp:
            #     fp.write( sv.to_csv() )

            if organism == 'ecoli':
                table = fluxes.to_numpy()
                file_path = os.path.join(result_dir,"flux.csv")
                expected_table = pandas.read_csv(file_path, index_col=0, header=0).to_numpy()
                table = numpy.array(table, dtype=float)
                expected_table = numpy.array(expected_table, dtype=float)
                self.assertTrue( numpy.isclose(table,expected_table,rtol=1e-03).all() )

                print(fluxes.loc[["ecoli_BIOMASS_Ecoli_core_w_GAM"],:])
            else:
                print(fluxes.loc[["olga_Biomass"],:])

            bio = proto.output["annotated_biomodel"]
            print(bio.to_json())
   
        e = proto.create_experiment(study=GTest.study, user=GTest.user)
        e.on_end(_on_end)
        asyncio.run( e.run() )