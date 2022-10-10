
import json
import os
import unittest

import numpy
import pandas
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, Settings, TaskRunner
from gws_gena import (Context, ContextImporter, FlatTwin, Network,
                      NetworkImporter, Twin, TwinReducer)
from pandas import DataFrame

settings = Settings.retrieve()


class TestTwinReducer(BaseTestCaseUsingFullBiotaDB):

    async def test_twin_reducer(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "bastin")

        net = NetworkImporter.call(
            File(path=os.path.join(data_dir, "bastin_network.json")),
            ConfigParams()
        )
        ctx = ContextImporter.call(
            File(path=os.path.join(data_dir, "bastin_context_reduce.json")),
            ConfigParams()
        )

        twin = Twin()
        twin.add_network(net)
        twin.add_context(ctx, related_network=net)

        tester = TaskRunner(
            params={},  # {"reversible_reactions": ["network_v1", "network_v18"]},
            inputs={"twin": twin},
            task_type=TwinReducer
        )
        outputs = await tester.run()

        efm = outputs["efm_table"]
        K = outputs["reduction_table"]

        file = os.path.join(data_dir, "./reduction/efm.csv")
        expected_efm: DataFrame = pandas.read_csv(file, index_col=0, encoding="utf-8")
        # self.assertEqual(efm.get_data().shape, expected_efm.shape)

        # cols = expected_efm.columns.tolist()
        # efm = efm.get_data().loc[:, cols]
        # self.assertTrue(efm.equals(expected_efm))

        file = os.path.join(data_dir, "./reduction/K.csv")
        expected_K = pandas.read_csv(file, index_col=0)
        # self.assertEqual(K.get_data().shape, expected_K.shape)

        print('\n--- EFM Bastin & Provost ---')
        print(efm)

        print('\n--- Reduced Bastin & Provost ---')
        print(K)
