import os
from gws_gena.cobra.conversion_annotation.conversion_annotation import ConvertAnnotation
from gws_core import (File,TaskRunner,Table,TableImporter,BaseTestCase,Settings)

settings = Settings.get_instance()

class TestConvertAnnotation(BaseTestCase):
    def test_convert_annotation(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        ## Lactococcus lactis case ##
        self.print(f"Test convert annotation : Lactococcus lactis")
        #load genes:
        model_input= File(os.path.join(data_dir, "cobra/convert_annotation/iNF517.json"))
        #create the TaskRunner
        runner_convert_annotation = TaskRunner(task_type=ConvertAnnotation,
                                inputs={'input_model':  model_input},
                                params = { "metabolites_id": "Other",
                                        "metabolites_name": "Literal_name",
                                        "reaction_id": "BiGG",
                                        "reaction_name": "Other"})
        #execute the TaskRunner
        outputs_convert_annotation = runner_convert_annotation.run()

        #check if we obtain the same output table
        table = outputs_convert_annotation['output_results']
        self.assertEqual([56],table.get_column_data("Rhea filled"))
        self.assertEqual([754],table.get_column_data("Number reactions"))
        self.assertEqual([375],table.get_column_data("EC number filled"))
        self.assertEqual([650],table.get_column_data("Number metabolites"))
        self.assertEqual([9],table.get_column_data("ChEBI filled"))

