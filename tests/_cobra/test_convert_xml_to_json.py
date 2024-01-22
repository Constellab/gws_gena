import json

from gws_gena.cobra.network_convert.convert_xml_to_json import ConvertXmlToJson
from gws_core import (File,TaskRunner)
from gws_core import BaseTestCase

class TestConvertXmlToJson(BaseTestCase):
    def test_convert_xml_to_json(self):
        #create a xml model :
        xml_model = "/lab/user/bricks/gws_gena/tests/testdata/cobra/network_convert/e_coli_core.xml"
        xml_model = File(xml_model)

        #create the TaskRunner
        runner_xml = TaskRunner(task_type=ConvertXmlToJson, inputs={'input_file': xml_model})

        #execute the TaskRunner
        outputs_xml = runner_xml.run()

        #retrieve the output model
        model_output_xml : File = outputs_xml['output_json_file']

        #import the expected model to compare it to the TaskRunner result.
        expected_model_xml = "/lab/user/bricks/gws_gena/tests/testdata/cobra/network_convert/model_xml.json"

        #Compare the two model using an assert function :
        with open(model_output_xml.path, 'r', encoding="utf-8") as model:
            data_output_xml  = json.load(model)

        with open(expected_model_xml, 'r', encoding="utf-8") as model:
            data_expected_xml  = json.load(model)

        self.assertTrue('D-Glucose' in data_expected_xml["metabolites"][0]["name"])
        self.assertTrue('D-Glucose' in data_output_xml["metabolites"][0]["name"])
        self.assertDictEqual(data_output_xml,data_expected_xml)

    def test_convert_mat_to_json(self):
        #create a mat model :
        mat_model = "/lab/user/bricks/gws_gena/tests/testdata/cobra/network_convert/e_coli_core.mat"
        mat_model = File(mat_model)

        #create the TaskRunner
        runner_mat = TaskRunner(task_type=ConvertXmlToJson, inputs={'input_file': mat_model})
        test = runner_mat.add_log_observer()

        #execute the TaskRunner
        outputs_mat = runner_mat.run()

        #retrieve the output model
        model_output_mat : File = outputs_mat['output_json_file']

        #import the expected model to compare it to the TaskRunner result.
        expected_model_mat = "/lab/user/bricks/gws_gena/tests/testdata/cobra/network_convert/model_mat.json"

        #Compare the two model using an assert function :
        with open(model_output_mat.path, 'r', encoding="utf-8") as model:
            data_output_mat  = json.load(model)

        with open(expected_model_mat, 'r', encoding="utf-8") as model:
            data_expected_mat  = json.load(model)

        self.assertTrue('D-Glucose' in data_expected_mat["metabolites"][0]["name"])
        self.assertTrue('D-Glucose' in data_output_mat["metabolites"][0]["name"])
        self.assertDictEqual(data_output_mat,data_expected_mat)
