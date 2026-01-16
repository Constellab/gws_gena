import os

import pandas
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, TaskRunner
from gws_gena import ContextImporter, DataProvider, NetworkImporter, Twin, TwinReducer
from pandas import DataFrame


class TestTwinReducer(BaseTestCaseUsingFullBiotaDB):
    def test_twin_reducer(self):
        data_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(data_dir, "bastin")

        net = NetworkImporter.call(
            File(path=os.path.join(data_dir, "bastin_network.json")), {"add_biomass": True}
        )
        ctx = ContextImporter.call(
            File(path=os.path.join(data_dir, "bastin_context_reduce.json")), {}
        )

        twin = Twin()
        twin.add_network(net)
        twin.add_context(ctx, related_network=net)

        tester = TaskRunner(
            params={},  # {"reversible_reactions": ["network_v1", "network_v18"]},
            inputs={"twin": twin},
            task_type=TwinReducer,
        )
        outputs = tester.run()

        efm = outputs["efm_table"]
        k = outputs["reduction_table"]

        file = os.path.join(data_dir, "./reduction/efm.csv")
        expected_efm: DataFrame = pandas.read_csv(file, index_col=0, encoding="utf-8")
        self.assertEqual(efm.get_data().shape, expected_efm.shape)

        # cols = expected_efm.columns.tolist()
        # efm = efm.get_data().loc[:, cols]
        # self.assertTrue(efm.equals(expected_efm))

        file = os.path.join(data_dir, "./reduction/K.csv")
        expected_k = pandas.read_csv(file, index_col=0)
        self.assertEqual(k.get_data().shape, expected_k.shape)

        self.print("\n--- EFM Bastin & Provost ---")
        self.print(efm)

        self.print("\n--- Reduced Bastin & Provost ---")
        self.print(k)
