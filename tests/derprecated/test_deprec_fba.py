import os, json
import pandas
import numpy

from gws_core import Settings, GTest, IExperiment, ExperimentService, File
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_gena import DeprecFBAProto

settings = Settings.retrieve()

class TestFba(BaseTestCaseUsingFullBiotaDB):
    
    async def test_fba(self):
        self.print("Test DeprecFBAProto")
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        async def run_fba( organism, number_of_randomizations=1 ):
            experiment = IExperiment(DeprecFBAProto)
            proto = experiment.get_protocol()
            
            organism_dir = os.path.join(data_dir, organism)
            network_file = File()
            network_file.path = os.path.join(organism_dir, f"{organism}.json")
            ctx_file = File()
            ctx_file.path = os.path.join(organism_dir, f"{organism}_context.json")
 
            proto.set_input("network_file", network_file)
            proto.set_input("context_file", ctx_file)

            fba = proto.get_process("fba")
            fba.set_param("number_of_randomizations", number_of_randomizations)
            fba.set_param("use_hard_bounds", True)
            fba.set_param("verbose", False)

            await experiment.run()

            # test results
            result = proto.get_output("fba_result")
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


        await run_fba( organism="toy", number_of_randomizations=1  )
        await run_fba( organism="toy", number_of_randomizations=100 )
        await run_fba( organism="ecoli", number_of_randomizations=100 )

        