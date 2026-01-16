import json
import os

from gws_core import BaseTestCase, File, Settings, TaskRunner
from gws_gena.cobra.network_convert.convert_xml_to_json import ConvertXmlToJson

settings = Settings.get_instance()

class TestConvertXmlToJson(BaseTestCase):
    def test_convert_xml_to_json(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        #create a xml model :
        xml_model= File(os.path.join(data_dir, "cobra/network_convert/e_coli_core.xml"))

        #create the TaskRunner
        runner_xml = TaskRunner(task_type=ConvertXmlToJson, inputs={'input_file': xml_model})

        #execute the TaskRunner
        outputs_xml = runner_xml.run()

        #retrieve the output model
        model_output_xml : File = outputs_xml['output_json_file']

        #import the expected model to compare it to the TaskRunner result.
        expected_model_xml = os.path.join(data_dir, "cobra/network_convert/model_xml.json")

        #Compare the two model using an assert function :
        with open(model_output_xml.path, encoding="utf-8") as model:
            data_output_xml  = json.load(model)

        with open(expected_model_xml, encoding="utf-8") as model:
            data_expected_xml  = json.load(model)

        self.assertTrue('D-Glucose' in data_expected_xml["metabolites"][0]["name"])
        self.assertTrue('D-Glucose' in data_output_xml["metabolites"][0]["name"])
        self.assertDictEqual(data_output_xml,data_expected_xml)

    def test_convert_mat_to_json(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        #create a mat model :
        mat_model= File(os.path.join(data_dir, "cobra/network_convert/e_coli_core.mat"))

        #create the TaskRunner
        runner_mat = TaskRunner(task_type=ConvertXmlToJson, inputs={'input_file': mat_model})
        test = runner_mat.add_log_observer()

        #execute the TaskRunner
        outputs_mat = runner_mat.run()

        #retrieve the output model
        model_output_mat : File = outputs_mat['output_json_file']

        #import the expected model to compare it to the TaskRunner result.
        expected_model_mat = os.path.join(data_dir, "cobra/network_convert/model_mat.json")

        #Compare the two model using an assert function :
        with open(model_output_mat.path, encoding="utf-8") as model:
            data_output_mat  = json.load(model)

        with open(expected_model_mat, encoding="utf-8") as model:
            data_expected_mat  = json.load(model)

        self.assertTrue('D-Glucose' in data_expected_mat["metabolites"][0]["name"])
        self.assertTrue('D-Glucose' in data_output_mat["metabolites"][0]["name"])
        self.assertDictEqual(data_output_mat,data_expected_mat)
