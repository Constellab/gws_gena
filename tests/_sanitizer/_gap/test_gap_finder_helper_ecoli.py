import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, Settings
from gws_gena import GapFinderHelper, NetworkImporter

settings = Settings.get_instance()


class TestGapFinder(BaseTestCaseUsingFullBiotaDB):

    def test_gap_finder_ecoli(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        organism_dir = os.path.join(data_dir, "ecoli")
        file_path = os.path.join(organism_dir, f"ecoli.json")
        net = NetworkImporter.call(
            File(path=file_path),
            ConfigParams()
        )

        helper = GapFinderHelper()
        dead = helper.find_deadend_compound_ids(net)
        orphans = helper.find_orphan_compound_ids(net)
        self.assertEquals(len(dead), 0)
        self.assertEquals(len(orphans), 0)

    def test_gap_finder_ecoli_without_AKGDH(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        organism_dir = os.path.join(data_dir, "ecoli")
        file_path = os.path.join(organism_dir, "./gaps/ecoli_without_AKGDH.json")
        net = NetworkImporter.call(
            File(path=file_path),
            ConfigParams()
        )

        helper = GapFinderHelper()
        dead = helper.find_deadend_compound_ids(net)
        orphans = helper.find_orphan_compound_ids(net)
        self.assertEquals(len(dead), 1)
        self.assertEquals(len(orphans), 0)
