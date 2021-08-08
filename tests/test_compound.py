
import os, json
import unittest
from pandas import DataFrame

from gws.unittest import GTest
from gws.settings import Settings
settings = Settings.retrieve()

from gena import Compound, Reaction, Network
from gena import Context, BioModel
from gena import BiomassTable

from biota.base import DbManager as BiotaDbManager

class TestNetwork(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()
        BiotaDbManager.use_prod_db(True)
     
    @classmethod
    def tearDownClass(cls):
        BiotaDbManager.use_prod_db(False)
        GTest.drop_tables()
    
    def test_compound(self):
        GTest.print("Test Compound")

        t = Network()     

        print( Network.full_classname() )
        print( BiomassTable.full_classname() )   

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
    