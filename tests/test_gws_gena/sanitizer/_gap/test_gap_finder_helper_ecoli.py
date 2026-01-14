import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings
from gws_gena import DataProvider, GapFinderHelper, NetworkImporter

settings = Settings.get_instance()


class TestGapFinder(BaseTestCaseUsingFullBiotaDB):
    def test_gap_finder_ecoli(self):
        data_dir = DataProvider.get_test_data_dir()
        organism_dir = os.path.join(data_dir, "ecoli")
        file_path = os.path.join(organism_dir, "ecoli.json")
        net = NetworkImporter.call(File(path=file_path), {"add_biomass": True})

        helper = GapFinderHelper()
        dead = helper.find_deadend_compound_ids(net)
        orphans = helper.find_orphan_compound_ids(net)
        self.assertEqual(len(dead), 0)
        self.assertEqual(len(orphans), 0)

    def test_gap_finder_ecoli_without_akgdh(self):
        data_dir = DataProvider.get_test_data_dir()
        organism_dir = os.path.join(data_dir, "ecoli")
        file_path = os.path.join(organism_dir, "./gaps/ecoli_without_AKGDH.json")
        net = NetworkImporter.call(File(path=file_path), {"add_biomass": True})

        helper = GapFinderHelper()
        dead = helper.find_deadend_compound_ids(net)
        orphans = helper.find_orphan_compound_ids(net)
        self.assertEqual(len(dead), 1)
        self.assertEqual(len(orphans), 0)
