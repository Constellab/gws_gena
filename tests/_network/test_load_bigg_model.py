import os
from gws_core import Settings, BaseTestCase, TaskRunner, File
from gws_gena.network.network_task.network_loader import LoadBiGGModels
from gws_gena import NetworkImporter

settings = Settings.get_instance()


class TestLoadBiggModel(BaseTestCase):

    def test_load_bigg_model(self):
        self.print("Test Load BiGG Model")

        runner_load_bigg_model = TaskRunner(task_type=LoadBiGGModels,
                                params = {'organism': "e_coli_core",
                                        'format': "json"})
        #execute the TaskRunner
        outputs_load_bigg_model = runner_load_bigg_model.run()

        #check if we retrieve the output
        model_output = outputs_load_bigg_model["output"]
        net_output = NetworkImporter.call(model_output, {"add_biomass" : True})

        #Get the expected network
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        net_expected_file = File(os.path.join(data_dir, "ecoli/ecoli.json"))
        net_expected = NetworkImporter.call(net_expected_file, {"add_biomass" : True})

        self.assertEqual(len(net_expected.reactions),len(net_output.reactions))
        self.assertEqual(len(net_expected.compounds),len(net_output.compounds))
