
from gws_core import TaskRunner, Table, BaseTestCase
from gws_gena import GenerationMultiSimulations
import pandas as pd

class TestGenerationMultiSimulations(BaseTestCase):

    def test_generation_multi_simulations(self):
        data = {"chemical": ["chemical", "chemical"],
            "replicat1": [2, 23],
            "replicat2": [1.5, 21.23],
            "replicat3": [3.5, 22.02]}
        df = pd.DataFrame(data)
        df.set_index("chemical", inplace=True)
        table_data = Table(df)

        # experiment
        tester = TaskRunner(
            inputs = {'experimental_data' : table_data},
            params={'number_simulations': 4, 'type_generation': "Multivariate normal distribution", "confidence_score": 1},
            task_type=GenerationMultiSimulations
        )
        outputs = tester.run()
        # test results
        simulations = outputs['simulations']

        self.assertTrue(simulations.column_exists("target"))
        self.assertTrue(simulations.column_exists("lower_bound"))
        self.assertTrue(simulations.column_exists("upper_bound"))
        self.assertTrue(simulations.column_exists("confidence_score"))
        self.assertEqual(simulations.get_column_data("confidence_score"), ['[1., 1., 1., 1.]', '[1., 1., 1., 1.]'])
