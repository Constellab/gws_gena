
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings, TaskRunner, TableImporter
from gws_gena import (Network, NetworkImporter,
                      TransporterAdder,TransformerMediumTable)

settings = Settings.get_instance()


class TestTransporterAdder(BaseTestCaseUsingFullBiotaDB):

    def test_transporter_adder(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "transporter_adder")

        medium_table = TableImporter.call(File(path=os.path.join(data_dir, "recon_medium.csv")), params={"index_column": -1})
        # run trainer
        tester = TaskRunner(
            inputs={"table": medium_table},
            task_type=TransformerMediumTable,
            params = {"entity_column": "Name of the metabolite",
                    "chebi_id_column": "Chebi ID"})

        medium_table = tester.run()['transformed_table']

        net: Network = NetworkImporter.call(
            File(path=os.path.join(data_dir, "recon_net.json")),
            params={'skip_orphans': True,"add_biomass" : True}
        )

        print(len(net.compounds))
        self.assertFalse("my_compound2" in net.compounds)
        self.assertFalse("Pyruvate" in net.compounds)

        tester = TaskRunner(
            inputs={
                'network': net,
                'medium_table': medium_table
            },
            params={},
            task_type=TransporterAdder
        )
        outputs = tester.run()
        net = outputs["network"]

        print(len(net.compounds))
        print(net.compounds.keys())
        self.assertTrue("my_compound2_extracellular space (theoretical supernatant)" in net.compounds)
        self.assertTrue("my_compound2_extracellular region (environment)" in net.compounds)
        self.assertTrue("CHEBI:15361_extracellular region (environment)" in net.compounds)
        self.assertTrue("CHEBI:15361_extracellular space (theoretical supernatant)" in net.compounds)

        file_path = os.path.join(data_dir, "extended_recon_net.csv")
        with open(file_path, 'w', encoding="utf-8") as f:
            f.write(net.to_csv())

        file_path = os.path.join(data_dir, "extended_recon_net.csv")
        with open(file_path, 'r', encoding="utf-8") as f:
            self.assertEqual(net.to_csv(), f.read())
