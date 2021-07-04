
import asyncio
import os, json
import unittest

from gws.model import *
from gws.settings import Settings
from gws.file import File
from gws.unittest import GTest

settings = Settings.retrieve()

from gena.network import Network
from gena.context import Context
from gena.biomodel import BioModel
from gena.fast_fba import FastFBA, FastFBAResult
from gena.fast_fba_proto import FastFBAProto

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

    def test_small_fba(self):
        return
        data_dir = settings.get_dir("gena:testdata_dir")

        def run_fba(context):
            proto = FastFBAProto()
            file_path = os.path.join(data_dir, "toy_network.json")
            try:
                network_file = File.get(File.path == file_path)
            except:
                network_file = File(path=file_path)
            proto.input["network_file"] = network_file

            if context:
                file_path = os.path.join(data_dir, "toy_context.json")
            else:
                file_path = os.path.join(data_dir, "toy_context_empty.json")
            
            try:
                ctx_file = File.get(File.path == file_path)
            except:
                ctx_file = File(path=file_path)

            proto.input["context_file"] = ctx_file

            fba = proto.get_fba()
            fba.set_param('least_energy', False)
            #fba.set_param('fluxes_to_maximize', ["Network_RB"])

            def _on_end(*args, **kwargs):
                result = proto.output["fba_result"]
                print(result.render__fluxes__as_table())
                print(result.render__sv__as_table())
    
            e = proto.create_experiment(study=GTest.study, user=GTest.user)
            e.on_end(_on_end)
            asyncio.run( e.run() )

        
        GTest.print("Test FastFBAProto: Small metwork (With context)")
        run_fba(context=True)

        GTest.print("Test FastFBAProto: Small metwork (Without context)")
        run_fba(context=False)

    def test_large_fba(self):
        GTest.print("Test FBAProto: Medium or large metwork (typically Ecoli)")
        data_dir = settings.get_dir("gena:testdata_dir")

        proto = FastFBAProto()
        model = "olga"
        
        if model == 'ecoli':
            file_path = os.path.join(data_dir, "ecoli/ecoli-core.json")
            network_file = File(path=file_path)
            file_path = os.path.join(data_dir, "ecoli/ecoli-core_context.json")
            ctx_file = File(path=file_path)
        else:
            file_path = os.path.join(data_dir, "olga/olga.json")
            network_file = File(path=file_path)
            file_path = os.path.join(data_dir, "olga/olga_context.json")
            ctx_file = File(path=file_path)

        proto.input["network_file"] = network_file
        proto.input["context_file"] = ctx_file

        fba = proto.get_fba()
        fba.set_param('least_energy', False)
        # if model == 'ecoli':
        #     fba.set_param('fluxes_to_maximize', ["ecoli_BIOMASS_Ecoli_core_w_GAM:1.0"])
        # else:
        #     fba.set_param('fluxes_to_maximize', ["olga_Biomass:1.0"])

        def _on_end(*args, **kwargs):
            result = proto.output["fba_result"]
            
            fluxes = result.render__fluxes__as_table()
            print(fluxes)
            print(result.render__sv__as_table())
 
            if model == 'ecoli':
                print(fluxes.loc[["ecoli_BIOMASS_Ecoli_core_w_GAM"],:])
            else:
                print(fluxes.loc[["olga_Biomass"],:])

            bio = proto.output["annotated_biomodel"]
            print(bio.to_json())

        e = proto.create_experiment(study=GTest.study, user=GTest.user)
        e.on_end(_on_end)
        asyncio.run( e.run() )