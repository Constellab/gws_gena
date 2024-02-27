
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings, TaskRunner
from gws_gena import OrphanRemover, NetworkImporter

settings = Settings.get_instance()


class TestOrphanRemover(BaseTestCaseUsingFullBiotaDB):

    def test_orphan_remover(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        net = NetworkImporter.call(
            File(path=os.path.join(data_dir, "toy_with_orphan/toy_with_orphan.json")),
            {"add_biomass" : True}
        )

        runner_orphan_remover = TaskRunner(
            params={},
            inputs={"network": net},
            task_type=OrphanRemover
        )
        outputs = runner_orphan_remover.run()
        result = outputs["network"]

        self.assertTrue("X_orphan_c" not in result.compounds)
        self.assertTrue("X_fake_orphan_e" not in result.compounds)
