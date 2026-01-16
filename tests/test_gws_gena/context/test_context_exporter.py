import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File
from gws_gena import ContextExporter, ContextImporter, DataProvider


class TestContextExporter(BaseTestCaseUsingFullBiotaDB):
    def test_context_exporter(self):
        self.print("Test Context Exporter")
        data_dir = DataProvider.get_test_data_dir()
        data_dir = os.path.join(data_dir, "toy")
        file_path = os.path.join(data_dir, "toy_context.json")
        ctx = ContextImporter.call(File(path=file_path), params={})

        ## CASE JSON exporter ##
        self.print("Test json export")

        file_exporter = ContextExporter.call(
            ctx, params={"file_name": "context", "file_format": "json"}
        )
        self.assertTrue(file_exporter.is_json())
