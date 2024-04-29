

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_gena import Compartment


class TestCompartment(BaseTestCaseUsingFullBiotaDB):

    def test_compartment(self):
        compart = Compartment.create_biomass_compartment()
        self.assertEqual(compart.name, "biomass")
        self.assertEqual(compart.go_id, "GO:0016049")

        compart2 = Compartment.from_biota(go_id="GO:0016049")
        self.assertEqual(compart2.name, "biomass")
