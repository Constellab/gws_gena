
import os, json
import unittest

from gws.settings import Settings
settings = Settings.retrieve()
settings.use_prod_biota_db(True)

from gena.network import Compound, Reaction, Network
from gena.context import Context
from gena.biomodel import Biomodel

class TestNetwork(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Biomodel.drop_table()
        Biomodel.create_table()
        Context.drop_table()
        Context.create_table()
        Network.drop_table()
        Network.create_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Biomodel.drop_table()
        Context.drop_table()
        Network.drop_table()
        settings.use_prod_biota_db(False)
        pass
    
    def test_compound(self):
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
        
    def test_reaction(self):
        t = Network()
  
        rxn1 = Reaction()
        t.add_reaction(rxn1)
        
        comp1 = Compound(name="ATP", chebi_id="CHEBI:17234", compartment=Compound.COMPARTMENT_CYTOSOL)
        rxn1.add_substrate(comp1, -1)
        
        comp2 = Compound(name="ADP", chebi_id="CHEBI:17235", compartment=Compound.COMPARTMENT_NUCLEUS)
        rxn1.add_product(comp2, +1)
        
        comp3 = Compound(name="Creatine", chebi_id="CHEBI:17236", compartment=Compound.COMPARTMENT_CYTOSOL)
        rxn1.add_substrate(comp3, -1)
        
        comp4 = Compound(name="Phosphocreatine", chebi_id="CHEBI:17237", compartment=Compound.COMPARTMENT_NUCLEUS)
        rxn1.add_product(comp4, 1)
        rxn1.ec_number = "MyEnzyme"
        print(rxn1)
        self.assertRaises(Exception, rxn1.add_product, comp4, 2)
        self.assertEqual(str(rxn1), "(1) ATP_c + (1) Creatine_c <==(MyEnzyme)==> (1) ADP_n + (1) Phosphocreatine_n")
        
        rxn1.direction = "R"
        self.assertEqual(str(rxn1), "(1) ATP_c + (1) Creatine_c ==(MyEnzyme)==> (1) ADP_n + (1) Phosphocreatine_n")
        print(rxn1)
        
        rxn1.direction = "L"
        self.assertEqual(str(rxn1), "(1) ATP_c + (1) Creatine_c <==(MyEnzyme)== (1) ADP_n + (1) Phosphocreatine_n")
        print(rxn1)
        
        print("--->")
        rxns = Reaction.from_biota(rhea_id="RHEA:15133") 
        for rxn in rxns:
            print(rxn.id)
            print(rxn)
        
        
        print("--->")
        net = Network()
        rxns = Reaction.from_biota(ec_number="1.4.1.3", network=net, tax_id="42068", tax_search_method="bottom_up") 
        for rxn in rxns:
            print(rxn.id)
            print(rxn)
        
        print(net.as_json(prettify = True, stringify = True))
        
    def test_import(self):
        data_dir = settings.get_dir("gena:testdata_dir")
        file_path = os.path.join(data_dir, "small.json")
        
        with open(file_path) as f:
            data = json.load(f)
            tw = Network.from_json(data)
        
        _json = tw.dumps(stringify=True, prettify=True)
        print(_json)        
        print(tw.as_json())
        
        self.assertEqual(len(tw.compounds), 5)
        
        self.assertEqual(tw.compounds["glc__D_e"].id, "glc__D_e")
        self.assertEqual(tw.compounds["glc__D_e"].name, "D-Glucose")
        self.assertEqual(tw.compounds["glc__D_e"].compartment, "e")
        
        self.assertEqual(tw.compounds["atp_c"].id, "atp_c")
        self.assertEqual(tw.compounds["atp_c"].name, "ATP C10H12N5O13P3")
        self.assertEqual(tw.compounds["atp_c"].compartment, "c")
        
        
        self.assertEqual(len(tw.reactions), 2)
        
        self.assertEqual(str(tw.reactions["EX_glc__D_e"]), "(1.0) glc__D_e <==()==> *")
        self.assertEqual(str(tw.reactions["GLNabc"]), "(1.0) atp_c + (1.0) gln__L_e <==()==> (1.0) adp_c + (1.0) gln__L_c")
