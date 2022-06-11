
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, Settings, TaskRunner
from gws_gena import (Compound, Context, GapFiller, Network, NetworkImporter,
                      Reaction, Twin)

settings = Settings.retrieve()


class TestGapFinder(BaseTestCaseUsingFullBiotaDB):

    async def test_gap_finder(self):
        self.print("Test GapFiller")

        organism = "ecoli_with_gap"
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        file_path = os.path.join(data_dir, "ecoli", f"{organism}.json")
        net = NetworkImporter.call(
            File(path=file_path),
            # loads biota info to resolve ids matching -> will be handled automatically after
            ConfigParams({"loads_biota_info": True})
        )

        nb_gaps = 0
        info = net.get_gaps()
        for k in info["compounds"]:
            if info["compounds"][k]["is_dead_end"]:
                nb_gaps += 1
        print(f"Total number of dead-end: {nb_gaps} over {len(info['compounds'])} compounds")

        params = {'fill_each_gap_once': True}
        if organism == "pcys":
            params.update({'tax_id': "4751"})  # fungi
        else:
            params.update({'tax_id': "562"})  # ecoli
            # params.update({'tax_id', "2")})     #bacteria

        tester = TaskRunner(
            params=params,
            inputs={"network": net},
            task_type=GapFiller
        )
        outputs = await tester.run()

        # test results
        result = outputs["network"]
        dump_json = result.dumps()

        result_dir = os.path.join(data_dir, 'gap_filler')
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)

        # file_path = os.path.join(result_dir, organism, "ecoli_gap_filled.json")
        # with open(file_path, 'w', encoding="utf-8") as fp:
        #     json.dump(result.dumps(), fp)

        file_path = os.path.join(result_dir, organism, "ecoli_gap_filled.json")
        with open(file_path, 'r', encoding="utf-8") as fp:
            expected_json = json.load(fp)
            self.assertEquals(len(dump_json["metabolites"]), len(expected_json["metabolites"]))
            self.assertEquals(len(dump_json["reactions"]), len(expected_json["reactions"]))
            #self.assertEquals(result.dumps(), expected_json)
