from gws_core import BaseTestCase, File, Settings, TaskRunner
from gws_gena import DataProvider
from gws_gena.cobra.conversion_annotation.conversion_annotation import ConvertAnnotation

settings = Settings.get_instance()


class TestConvertAnnotation(BaseTestCase):
    def test_convert_annotation(self):
        ## Lactococcus lactis case ##
        self.print("Test convert annotation : Lactococcus lactis")
        # load genes:
        model_input = File(DataProvider.get_test_data_path("cobra/convert_annotation/iNF517.json"))
        # create the TaskRunner
        runner_convert_annotation = TaskRunner(
            task_type=ConvertAnnotation,
            inputs={"input_model": model_input},
            params={
                "metabolites_id": "Other",
                "metabolites_name": "Literal_name",
                "reaction_id": "BiGG",
                "reaction_name": "Other",
            },
        )
        # execute the TaskRunner
        outputs_convert_annotation = runner_convert_annotation.run()

        # check if we obtain the same output table
        table = outputs_convert_annotation["output_results"]
        self.assertEqual([0], table.get_column_data("Rhea filled"))
        self.assertEqual([754], table.get_column_data("Number reactions"))
        self.assertEqual([374], table.get_column_data("EC number filled"))
        self.assertEqual([650], table.get_column_data("Number metabolites"))
        self.assertEqual([0], table.get_column_data("ChEBI filled"))
