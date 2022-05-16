import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, Settings, TaskRunner
from gws_gena import (Compound, Context, GapFinder, Network, NetworkImporter,
                      Reaction, Twin)

settings = Settings.retrieve()


class TestGapFinder(BaseTestCaseUsingFullBiotaDB):

    async def test_gap_finder_toy(self):
        self.print("Test GapFinder")
        organism = "pcys"
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        organism_dir = os.path.join(data_dir, organism)
        result_dir = os.path.join(data_dir, "gap_finder", organism)

        file_path = os.path.join(organism_dir, f"{organism}.json")
        net = NetworkImporter.call(
            File(path=file_path),
            ConfigParams()
        )

        tester = TaskRunner(
            params={},
            inputs={"network": net},
            task_type=GapFinder
        )
        outputs = await tester.run()

        # test results
        result = outputs["result"]
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)

        self.assertEquals(result.count_number_of_dead_ends(), 688)
        self.assertEquals(result.count_number_of_orphans(), 0)

        print("Compounds:")
        print("------------")
        print(result.get_compounds_as_dataframe())
        file_path = os.path.join(result_dir, "compounds.csv")
        with open(file_path, 'w', encoding="utf-8") as fp:
            fp.write(result.get_compounds_as_dataframe().to_csv())

        print("Reactions:")
        print("------------")
        print(result.get_reactions_as_dataframe())
        file_path = os.path.join(result_dir, "reactions.csv")
        with open(file_path, 'w', encoding="utf-8") as fp:
            fp.write(result.get_reactions_as_dataframe().to_csv())

        print("Pathways:")
        print("------------")
        print(result.get_pathways_as_dataframe())
        file_path = os.path.join(result_dir, "pathways.csv")
        with open(file_path, 'w', encoding="utf-8") as fp:
            fp.write(result.get_pathways_as_dataframe().to_csv())

    async def test_gap_finder_ecoli(self):
        self.print("Test GapFinder")
        organism = "ecoli"
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        organism_dir = os.path.join(data_dir, organism)
        file_path = os.path.join(organism_dir, f"{organism}.json")
        net = NetworkImporter.call(
            File(path=file_path),
            ConfigParams()
        )

        tester = TaskRunner(
            params={},
            inputs={"network": net},
            task_type=GapFinder
        )
        outputs = await tester.run()
        result = outputs["result"]
        self.assertEquals(result.count_number_of_dead_ends(), 0)
        self.assertEquals(result.count_number_of_orphans(), 0)


    async def test_gap_finder_ecoli_with_gap(self):
        self.print("Test GapFinder")
        organism = "ecoli"
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        organism_dir = os.path.join(data_dir, organism)
        file_path = os.path.join(organism_dir, f"{organism}_with_gap.json")
        net = NetworkImporter.call(
            File(path=file_path),
            ConfigParams()
        )

        tester = TaskRunner(
            params={},
            inputs={"network": net},
            task_type=GapFinder
        )
        outputs = await tester.run()
        result = outputs["result"]
        self.assertEquals(result.count_number_of_dead_ends(), 3)
        self.assertEquals(result.count_number_of_orphans(), 0)
