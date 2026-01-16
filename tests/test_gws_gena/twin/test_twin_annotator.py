
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings, TaskRunner
from gws_gena import FBA, ContextImporter, NetworkImporter, Twin, TwinAnnotator, TwinBuilder

settings = Settings.get_instance()

class TestTwinAnnotator(BaseTestCaseUsingFullBiotaDB):

    def test_twin_annotator(self):
        self.print("Test Task Twin annotator")
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        #Perform a FBA
        organism = "ecoli"
        organism_dir = os.path.join(data_dir, organism)
        net = NetworkImporter.call(
            File(os.path.join(organism_dir, f"{organism}.json")),
            params={"add_biomass" : True}
        )
        ctx = ContextImporter.call(File(
            os.path.join(organism_dir, f"{organism}_context.json")
        ))

        tester_twin_builder = TaskRunner(
            params={},
            inputs={"network": net, "context": ctx},
            task_type=TwinBuilder
        )
        outputs_twin_builder = tester_twin_builder.run()

        twin = outputs_twin_builder["twin"]

        runner_fba = TaskRunner(task_type=FBA,
                                inputs={'twin': twin},
                                params = {'biomass_optimization': "maximize",
                                'qssa_relaxation_strength': 1,
                                'relax_qssa' : True,
                                'solver' : "quad"})
        #execute the TaskRunner
        outputs_fba = runner_fba.run()
        result = outputs_fba["fba_result"]

        #Run Task twin annotator
        runner_twin_annotator = TaskRunner(task_type=TwinAnnotator,
                                inputs={'twin': twin,
                                'metabolic_fluxes': result},
                                params = {})
        #execute the TaskRunner
        outputs_twin_annotator = runner_twin_annotator.run()
        twin_annotated = outputs_twin_annotator["twin"]

        self.assertTrue(isinstance(twin_annotated,Twin))
