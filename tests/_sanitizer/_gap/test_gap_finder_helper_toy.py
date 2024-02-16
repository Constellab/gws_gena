
import json
import os

import numpy
import pandas as pd
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, GTest, Settings
from gws_gena import (Context, ContextImporter, FlatTwin, GapFinderHelper,
                      Network, NetworkImporter, Twin, TwinHelper)
from pandas import DataFrame

settings = Settings.get_instance()


class TestDeadEndFinderHelper(BaseTestCaseUsingFullBiotaDB):

    def test_toy(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy")

        file_path = os.path.join(data_dir, "toy.json")
        net = NetworkImporter.call(
            File(path=file_path),
            params={}
        )

        helper = GapFinderHelper()
        df = helper.find_gaps(net)
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
            params={}
        )

        helper = GapFinderHelper()
        df = helper.find_gaps(net)
        comp_ids = [idx for idx in df.index if df.at[idx, "is_orphan"]]
        self.assertEqual(len(comp_ids), 0)

        comp_ids = [idx for idx in df.index if df.at[idx, "is_dead_end"]]
        self.assertEqual(comp_ids, ['X1_c', 'X2_c', 'X1_e', 'X2_e', 'X4_e', 'X5_e'])

    def test_toy_with_orphan(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "toy_with_orphan")

        file_path = os.path.join(data_dir, "toy_with_orphan.json")
        net = NetworkImporter.call(
            File(path=file_path),
            params={}
        )

        helper = GapFinderHelper()
        df = helper.find_gaps(net)
        comp_ids = [idx for idx in df.index if df.at[idx, "is_orphan"]]
        self.assertEqual(comp_ids, ['X_orphan_c', 'X_fake_orphan_e'])

        comp_ids = [idx for idx in df.index if df.at[idx, "is_dead_end"]]
        self.assertEqual(comp_ids, ['X1_e', 'X2_e', 'X4_e', 'X5_e', 'X_orphan_c', 'X_fake_orphan_e'])
