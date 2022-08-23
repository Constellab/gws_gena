
import json
import os

import numpy
import pandas as pd
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, GTest, Settings
from gws_gena import (Context, ContextImporter, GapFinderHelper, FlatTwin,
                      Network, NetworkImporter, Twin, TwinHelper)
from pandas import DataFrame

settings = Settings.retrieve()


class TestDeadEndFinderHelper(BaseTestCaseUsingFullBiotaDB):

    def test_toy(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")

        file_path = os.path.join(data_dir, "toy.json")
        net = NetworkImporter.call(
            File(path=file_path),
            params=ConfigParams()
        )

        helper = GapFinderHelper()
        df = helper.find(net)
        print(df)
        comp_ids = [idx for idx in df.index if df.at[idx, "is_orphan"]]
        self.assertEqual(len(comp_ids), 0)

        comp_ids = [idx for idx in df.index if df.at[idx, "is_dead_end"]]
        self.assertEqual(len(comp_ids), 0)

    def test_toy_with_gaps(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy_with_gap")

        file_path = os.path.join(data_dir, "toy_network.json")
        net = NetworkImporter.call(
            File(path=file_path),
            params=ConfigParams()
        )

        helper = GapFinderHelper()
        df = helper.find(net)
        comp_ids = [idx for idx in df.index if df.at[idx, "is_orphan"]]
        self.assertEqual(len(comp_ids), 0)

        comp_ids = [idx for idx in df.index if df.at[idx, "is_dead_end"]]
        self.assertEqual(comp_ids, ['X1_c', 'X2_c'])

    def test_toy_with_orphan(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy_with_orphan")

        file_path = os.path.join(data_dir, "toy_with_orphan.json")
        net = NetworkImporter.call(
            File(path=file_path),
            params=ConfigParams()
        )

        helper = GapFinderHelper()
        df = helper.find(net)
        comp_ids = [idx for idx in df.index if df.at[idx, "is_orphan"]]
        self.assertEqual(comp_ids, ["X_orphan_c"])

        comp_ids = [idx for idx in df.index if df.at[idx, "is_dead_end"]]
        self.assertEqual(comp_ids, ["X_orphan_c"])
