
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, Settings, TaskRunner
from gws_gena import (Compound, Context, GapFiller, GapFinderHelper, Network,
                      NetworkImporter, Reaction, Twin)

settings = Settings.get_instance()


class TestGapFinder(BaseTestCaseUsingFullBiotaDB):

    async def test_gap_filler_with_no_gaps(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        file_path = os.path.join(data_dir, "./ecoli/ecoli.json")
        net = NetworkImporter.call(
            File(path=file_path),
            ConfigParams({"translate_ids": True})
        )

        params = {"tax_id":  "562"}  # ecoli
        # params = {"tax_id":  "2"}  # bacteria

        tester = TaskRunner(
            params=params,
            inputs={"network": net},
            task_type=GapFiller
        )
        outputs = await tester.run()

        # test results
        result = outputs["network"]

        helper = GapFinderHelper()
        dead = helper.find_deadend_compound_ids(net)
        print(f"Before gap filling: {len(dead)} dead-end over {len(net.compounds)} compounds")
        dead = helper.find_deadend_compound_ids(result)
        print(f"After gap filling: {len(dead)} dead-end over {len(result.compounds)} compounds")

        print(dead)
