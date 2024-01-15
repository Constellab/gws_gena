
import json
import os
import unittest

import numpy
import pandas as pd
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, GTest, Settings
from gws_gena import (Context, ContextImporter, FlatTwin, Network,
                      NetworkImporter, Twin, TwinHelper)
from pandas import DataFrame

settings = Settings.get_instance()


class TestTwinReductionHelper(BaseTestCaseUsingFullBiotaDB):

    def test_bastin_twin(self):
        self.print("Test reduction helper")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "bastin")

        net = NetworkImporter.call(
            File(path=os.path.join(data_dir, "bastin_network.json")),
            {}
        )
        ctx = ContextImporter.call(
            File(path=os.path.join(data_dir, "bastin_context_reduce.json")),
            {}
        )

        twin = Twin()
        twin.add_network(net)
        twin.add_context(ctx, related_network=net)

        flat_twin = twin.flatten()
        mat = TwinHelper.compute_reduced_matrices(flat_twin)

        print('\n--- EFM Bastin & Provost ---')
        print(mat["EFM"])
        #file = os.path.join(data_dir, "./reduction/emf.csv")
        # mat["EFM"].to_csv(file)

        print('\n--- Reduced Bastin & Provost ---')
        print(mat["K"])
        #file = os.path.join(data_dir, "./reduction/K.csv")
        # mat["K"].to_csv(file)
