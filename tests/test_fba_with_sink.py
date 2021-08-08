
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
        data_dir = os.path.join(data_dir, "toy_with_gap")

        def run_fba(context, solver="highs", fill_gaps_with_sinks=True, relax_steady_state=False):
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
            fba.set_param("fill_gaps_with_sinks", fill_gaps_with_sinks)
            fba.set_param("relax_steady_state", relax_steady_state)

            def _on_end(*args, **kwargs):
                result = proto.output["fba_result"]
                fluxes = result.render__fluxes__as_table()
                sv = result.render__sv__as_table()
                print(fluxes)
                print(sv)
                
                fill_dir = "sink" if fill_gaps_with_sinks else "no_sink"
                relax_dir = "relax" if relax_steady_state else "no_relax"

                if context:
                    result_dir = os.path.join(data_dir, 'fba', solver, fill_dir, relax_dir)
                    if not os.path.exists(result_dir):
                        os.makedirs(result_dir)
                    #write test results in files
                    file_path = os.path.join(result_dir,"sv.csv")
                    with open(file_path, 'w') as fp:
                        fp.write(sv.to_csv())
                    file_path = os.path.join(result_dir,"flux.csv")
                    with open(file_path, 'w') as fp:
                        fp.write(fluxes.to_csv())
                    
                    table = fluxes.to_numpy()
                    file_path = os.path.join(result_dir,"flux.csv")
                    expected_table = pandas.read_csv(file_path, index_col=0, header=0).to_numpy()
                    table = numpy.array(table, dtype=float)
                    expected_table = numpy.array(expected_table, dtype=float)
                    #self.assertTrue( numpy.isclose(table,expected_table,rtol=1e-02).all() )
                bio = proto.output["annotated_biomodel"]
                net = list(bio.networks.values())[0]
                tflux = net.render__total_flux__as_table()
                print(tflux)

            e = proto.create_experiment(study=GTest.study, user=GTest.user)
            e.on_end(_on_end)
            asyncio.run( e.run() )

        # fill_with_sink = True, relax = False
        GTest.print("Test FBAProto: Small network (toy + context + linprog)")
        run_fba(context=True,solver="highs", fill_gaps_with_sinks=True)
        GTest.print("Test FBAProto: Small network (toy + context + quad)")
        run_fba(context=True,solver="quad", fill_gaps_with_sinks=True) 

        # fill_with_sink = False, relax = True
        GTest.print("Test FBAProto: Small network (toy + context + quad)")
        run_fba(context=True,solver="quad", fill_gaps_with_sinks=False, relax_steady_state=True) 