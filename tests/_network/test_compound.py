
import json
import os
import unittest

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_biota import Compound as BiotaCompound
from gws_core import GTest, Settings
from gws_gena import (BiomassReactionTable, Compound, Compartment, Network, Reaction, Twin)
from pandas import DataFrame


class TestNetwork(BaseTestCaseUsingFullBiotaDB):

    def test_compound(self):
        self.print("Test Compound")
        comp1 = Compound(dict(name="gluc", compartment=Compartment.CYTOSOL, chebi_id="CHEBI:17234"))
        bc1 = comp1.get_related_biota_compound()
        self.assertEqual(bc1.name, "glucose")
        self.assertEqual(bc1.kegg_id, "C00293")
        self.assertEqual(bc1.charge, 0)
        self.assertEqual(bc1.mass, 180.15588)
        self.assertEqual(bc1.monoisotopic_mass, 180.06339)

        comp2 = Compound(dict(name="gluc2", compartment=Compartment.CYTOSOL))
        comp2.kegg_id = "C00293"
        bc2 = comp2.get_related_biota_compound()
        self.assertEqual(bc2.name, "glucose")
        self.assertEqual(bc2.chebi_id, "CHEBI:17234")
        self.assertEqual(bc2.charge, 0)
        self.assertEqual(bc2.mass, 180.15588)
        self.assertEqual(bc2.monoisotopic_mass, 180.06339)

        comp3 = Compound.from_biota(kegg_id="C00293")
        self.assertEqual(comp3.monoisotopic_mass, 180.06339)