import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, Settings, TaskRunner
from gws_gena import (Compound, GapFinder, Network, NetworkImporter, Reaction,
                      Twin, TwinContext)

settings = Settings.retrieve()


class TestGapFinder(BaseTestCaseUsingFullBiotaDB):

    async def test_gap_finderer(self):
        self.print("Test GapFinder")
        organism = "pcys"
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

        # test results
        result = outputs["result"]
        result_dir = os.path.join(organism_dir, 'gap_finder')
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)

        print("Compounds:")
        print("------------")
        print(result.get_compounds_as_table())
        file_path = os.path.join(result_dir, "compounds.csv")
        with open(file_path, 'w') as fp:
            fp.write(result.get_compounds_as_table().to_csv())

        print("Reactions:")
        print("------------")
        print(result.get_reactions_as_table())
        file_path = os.path.join(result_dir, "reactions.csv")
        with open(file_path, 'w') as fp:
            fp.write(result.get_reactions_as_table().to_csv())

        print("Pathways:")
        print("------------")
        print(result.get_pathways_as_table())
        file_path = os.path.join(result_dir, "pathways.csv")
        with open(file_path, 'w') as fp:
            fp.write(result.get_pathways_as_table().to_csv())
