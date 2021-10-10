import os, json

from gws_core import Settings, GTest, IExperiment, File
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_gena import DeprecFBAProto

settings = Settings.retrieve()

class TestFba(BaseTestCaseUsingFullBiotaDB):

    async def test_fba(self):
        self.print("Test DeprecFBAProto")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy_gap")

        experiment = IExperiment(DeprecFBAProto)
        proto = DeprecFBAProto()
        
        file_path = os.path.join(data_dir, "toy.json")
        network_file = File(path=file_path)
        file_path = os.path.join(data_dir, "toy_context.json")
        ctx_file = File(path=file_path)


        proto.set_input("network_file", network_file)
        proto.set_input("context_file", ctx_file)

        fba = proto.get_fba()
        fba.set_param("least_energy_weight", 0)
        fba.set_param("number_of_randomizations", 1)
        fba.set_param("use_hard_bounds", True)
        fba.set_param("verbose", True)

        # run experiment
        experiment: Experiment = Experiment(
            protocol=proto, study=GTest.study, user=GTest.user)
        experiment.save()
        experiment = await ExperimentService.run_experiment(
            experiment=experiment, user=GTest.user)

        # test results
        f = proto.output["fba_file"]
        result_dir = os.path.join(data_dir, 'fba')
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)

        file_path = os.path.join(result_dir, "result.json")
        with open(file_path) as fp:
            expected_result_content = json.load(fp)          
            result_content = f.to_json(deep=True)["data"]["content"]
            self.assertEqual( result_content, expected_result_content  )
        
        #print(f.render__stoich_matrix__as_table())
        #print(f.render__solver_success__as_table())
        #print(f.render__ker_of_identif__as_table())
        #print(f.render__ker_of_intern_stoich__as_table())
        #print(f.render__sv_distrib__as_table())
        #print(f.render__flux_distrib__as_table())
        print(f.render__flux_ranges__as_table())
        print(f.render__sv_ranges__as_table())
        #print(f.render__feasible_fluxes__as_table())

        bio = proto.output["annotated_twin"]
        net = list(bio.networks.values())[0]
        tflux = net.render__total_flux__as_table()
        print(tflux)
