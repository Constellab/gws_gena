
import os, json
import unittest
from pandas import DataFrame

from gws.unittest import GTest
from gws.settings import Settings
settings = Settings.retrieve()

from gena import Compound, Reaction, Network
from gena import BioModel, Context

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

    def test_reaction(self):
        GTest.print("Test Reaction")

        t = Network()
  
        rxn1 = Reaction(id="my-reaction")
        t.add_reaction(rxn1)
        
        comp1 = Compound(name="ATP", chebi_id="CHEBI:17234", compartment=Compound.COMPARTMENT_CYTOSOL)
        rxn1.add_substrate(comp1, -1)
        
        comp2 = Compound(name="ADP", chebi_id="CHEBI:17235", compartment=Compound.COMPARTMENT_NUCLEUS)
        rxn1.add_product(comp2, +1)
        
        comp3 = Compound(name="Creatine", chebi_id="CHEBI:17236", compartment=Compound.COMPARTMENT_CYTOSOL)
        rxn1.add_substrate(comp3, -1)
        
        comp4 = Compound(name="Phosphocreatine", chebi_id="CHEBI:17237", compartment=Compound.COMPARTMENT_NUCLEUS)
        rxn1.add_product(comp4, 1)
        rxn1.enzyme = {"ec_number": "MyEnzyme"}
        
        print(rxn1.to_str())
        self.assertRaises(Exception, rxn1.add_product, comp4, 2)
        self.assertEqual(rxn1.to_str(), "(1.0) ATP_c + (1.0) Creatine_c <==(MyEnzyme)==> (1.0) ADP_n + (1.0) Phosphocreatine_n")
        
        rxn1.direction = "R"
        self.assertEqual(rxn1.to_str(), "(1.0) ATP_c + (1.0) Creatine_c ==(MyEnzyme)==> (1.0) ADP_n + (1.0) Phosphocreatine_n")
        print(rxn1.to_str())
        
        rxn1.direction = "L"
        self.assertEqual(rxn1.to_str(), "(1.0) ATP_c + (1.0) Creatine_c <==(MyEnzyme)== (1.0) ADP_n + (1.0) Phosphocreatine_n")
        print(rxn1.to_str())
        
        print("--->")
        rxns = Reaction.from_biota(rhea_id="RHEA:15133") 
        for rxn in rxns:
            print(rxn.id)
            print(rxn.to_str())
            print(f"Mass/charge balance: {rxn.compute_mass_and_charge_balance()}")
        
        print("--->")
        net = Network()
        rxns = Reaction.from_biota(ec_number="1.4.1.3", network=net, tax_id="42068", tax_search_method="bottom_up") 
        for rxn in rxns:
            print(rxn.id)
            print(rxn.to_str())
            print(f"Mass/charge balance: {rxn.compute_mass_and_charge_balance()}")

        print("--->")
        sink_rxn = Reaction.create_sink_reaction(related_compound=comp4)
        print(sink_rxn.to_str())
