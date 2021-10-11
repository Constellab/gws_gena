
import os, json

from gws_core import Settings, TaskTester, File
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_gena import Network, TwinContext, Twin, GapFiller, Compound, Reaction 

settings = Settings.retrieve()

class TestGapFinder(BaseTestCaseUsingFullBiotaDB):

    async def test_gap_finder(self):
        self.print("Test GapFiller")
        async def run_gap_fill(organism):
            data_dir = settings.get_variable("gws_gena:testdata_dir")
            file_path = os.path.join(data_dir, organism, f"{organism}.json")
            net = Network.import_from_path(file_path)
   
            nb_gaps = 0
            info = net._get_gap_info()
            for k in info["compounds"]:
                if info["compounds"][k]["is_gap"]:
                    nb_gaps += 1
            print(f"Total number of gaps: {nb_gaps} over {len(info['compounds'])} compounds")

            params = {'add_sink_reactions': True}
            if organism == "pcys":
                params.update({'tax_id': "4751"})    #fungi
            else:
                params.update({'tax_id': "562"})     #ecoli
                #params.update({'tax_id', "2")})     #bacteria

            tester = TaskTester(
                params = params,
                inputs = {"network": net},
                task_type = GapFiller
            )
            outputs = await tester.run()

            # test results
            result = outputs["network"]
            result_dir = os.path.join(data_dir, 'gap_filler')
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)
            
            file_path = os.path.join(result_dir, f"{organism}.json")
            with open(file_path, 'w') as fp:
                json.dump(result.dumps(), fp)

            # file_path = os.path.join(result_dir, f"{organism}.json")
            # with open(file_path, 'r') as fp:
            #     expected_json = json.load(fp)
            #     self.assertEquals(result.dumps(), expected_json)

        await run_gap_fill("ecoli_gap")
