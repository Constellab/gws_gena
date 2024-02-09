
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings, TaskRunner
from gws_gena import BiomassReactionTableImporter


class TestBiomassReactionTableImporter(BaseTestCaseUsingFullBiotaDB):

    def test_importer(self):
        settings = Settings.get_instance()
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        # run trainer
        tester = TaskRunner(
            params={"entity_column": "Component",
                "chebi_column": "Chebi ID",
                "biomass_column": "Biomass"},
            inputs={"source": File(path=os.path.join(data_dir, "./recon/recon_biomass.csv"))},
            task_type=BiomassReactionTableImporter
        )

        outputs = tester.run()
        biomass_reaction = outputs['target']

        self.assertEqual(biomass_reaction.get_data().iloc[0, 0], "Biomass")
        self.assertEqual(biomass_reaction.get_data().iloc[3, 2], -0.025990654)
