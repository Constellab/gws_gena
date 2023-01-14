
import json
import os
import unittest

import numpy
import pandas
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, Settings, TaskRunner
from gws_gena import IsolateFinder, Network, NetworkImporter
from pandas import DataFrame

settings = Settings.get_instance()


class TestIsolateFinder(BaseTestCaseUsingFullBiotaDB):

    async def test_isolate_finder_ecoli(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "ecoli")

        net = NetworkImporter.call(
            File(path=os.path.join(data_dir, "ecoli.json")),
            ConfigParams()
        )

        tester = TaskRunner(
            params=ConfigParams({}),
            inputs={"network": net},
            task_type=IsolateFinder
        )
        outputs = await tester.run()
        result = outputs["result"]

        self.assertEqual(result.get_reaction_table().nb_rows, 0)
        self.assertEqual(result.get_compound_table().nb_rows, 0)

    async def test_isolate_finder_pcys(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "pcys")

        net = NetworkImporter.call(
            File(path=os.path.join(data_dir, "pcys.json")),
            ConfigParams()
        )

        tester = TaskRunner(
            params=ConfigParams({}),
            inputs={"network": net},
            task_type=IsolateFinder
        )
        outputs = await tester.run()
        result = outputs["result"]

        self.assertEqual(result.get_reaction_table().nb_rows, 105)
        self.assertEqual(result.get_compound_table().nb_rows, 211)

        print(result.get_compound_table())

        print(result.get_reaction_table())
