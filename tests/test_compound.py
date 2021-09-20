
import os, json
import unittest
from pandas import DataFrame

from gws_core import Settings, GTest
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_gena import Compound, Reaction, Network, TwinContext, Twin, BiomassTable

class TestNetwork(BaseTestCaseUsingFullBiotaDB):
    
    def test_compound(self):
        self.print("Test Compound")

        t = Network()     
        comp1 = Compound(name="gluc", network=t, compartment=Compound.COMPARTMENT_CYTOSOL, chebi_id="CHEBI:17234")
        
        bc1 = comp1.get_related_biota_compound()
        self.assertEqual(bc1.name, "glucose")
        self.assertEqual(bc1.kegg_id, "C00293")
        self.assertEqual(bc1.charge, 0)
        self.assertEqual(bc1.mass, 180.15588)
        self.assertEqual(bc1.monoisotopic_mass, 180.06339)
        
        comp2 = Compound(name="gluc2", compartment=Compound.COMPARTMENT_CYTOSOL)
        t.add_compound(comp2)
        comp2.kegg_id = "C00293"
        bc2 = comp2.get_related_biota_compound()
        self.assertEqual(bc2.name, "glucose")
        self.assertEqual(bc2.chebi_id, "CHEBI:17234")
        self.assertEqual(bc2.charge, 0)
        self.assertEqual(bc2.mass, 180.15588)
        self.assertEqual(bc2.monoisotopic_mass, 180.06339)
        
        comp3 = Compound.from_biota(kegg_id="C00293")
        self.assertEqual(comp3.monoisotopic_mass, 180.06339)

        S = t.create_stoichiometric_matrix()
        print(S)
    