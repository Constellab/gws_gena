
import json
import os

import numpy
import pandas as pd
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import (File, GTest, Settings,TaskRunner)
from gws_gena import (Context, ContextImporter, FlatTwin, Network,
                      NetworkImporter, Twin, TwinHelper, TwinExporter,TwinBuilder)
from pandas import DataFrame

settings = Settings.get_instance()

class TestTwinExporter(BaseTestCaseUsingFullBiotaDB):

    def test_twin_exporter(self):
        self.print(f"Test Task Twin exporter")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "small_net")

        file_path = os.path.join(data_dir, "small_net.json")
        net = NetworkImporter.call(
            File(path=file_path),
            params={"skip_orphans": True}
        )

        file_path = os.path.join(data_dir,"small_context.json")
        ctx = ContextImporter.call(
            File(path=file_path),
            params={}
            )


        runner = TaskRunner(task_type=TwinBuilder,
                                inputs={'network':  net, "context" : ctx})

        outputs = runner.run()
        twin = outputs["twin"]

        ## CASE JSON exporter ##
        self.print(f"Test json export")
        twin_exporter = TwinExporter.call(
            twin,
            params={'file_name': "twin",
                    'file_format': "json"})


        self.assertTrue(twin_exporter.is_json())
