import os

from gws_core import BaseTestCase, File, Settings, Table, TableImporter, TaskRunner
from gws_gena.fba.flux_table_analysis.plot_flux_table_analysis import PlotFluxTableAnalysis

settings = Settings.get_instance()


class TestPlotFluxTableAnalysis(BaseTestCase):
    def test_flux_table_analysis(self):
        testdata_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(testdata_dir, "fba", "flux_table_analysis")

        # load flux tables :
        flux_table_1 = os.path.join(data_dir, "Flux_table_ecoli_1.csv")
        flux_table_1 = TableImporter.call(File(path=flux_table_1), params={"index_column": 0})
        flux_table_2 = os.path.join(data_dir, "Flux_table_ecoli_2.csv")
        flux_table_2 = TableImporter.call(File(path=flux_table_2), params={"index_column": 0})
        # load reactions modified :
        reactions_modified = os.path.join(data_dir, "reactions_modified.csv")
        reactions_modified = File(reactions_modified)

        # create the TaskRunner
        runner_flux_analysis = TaskRunner(task_type=PlotFluxTableAnalysis,
                                          inputs={'flux_table_condition1':  flux_table_1,
                                                  'flux_table_condition2':  flux_table_2,
                                                  'file_modified_reactions': reactions_modified},
                                          params={'name_condition1': "coli_1",
                                                  'name_condition2': "coli_2",
                                                  'pattern': "network_",
                                                  'column_reaction_id': "reaction_id",
                                                  'threshold': 2,
                                                  'log_x': False,
                                                  'log_y': False})

        # execute the TaskRunner
        outputs_flux_analysis = runner_flux_analysis.run()

        # retrieve one of the output : the table
        table_output_flux_analysis: Table = outputs_flux_analysis['table_changes']

        # import the expected table to compare it to the TaskRunner result.
        expected_table = os.path.join(data_dir, "expected_output_table.csv")
        # expected_table = File(expected_table)
        expected_table = TableImporter.call(File(path=expected_table))

        table_output_flux_analysis = table_output_flux_analysis.get_data()
        expected_table = expected_table.get_data()
        table_output_flux_analysis = table_output_flux_analysis.reset_index(drop=True)
        expected_table = expected_table.reset_index(drop=True)
        expected_table = expected_table.to_dict()
        table_output_flux_analysis = table_output_flux_analysis.to_dict()
        self.assertDictEqual(table_output_flux_analysis, expected_table)
