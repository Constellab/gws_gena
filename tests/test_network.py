
import os, json
import unittest
from pandas import DataFrame

from gws.settings import Settings
settings = Settings.retrieve()

from gena.network import Compound, Reaction, Network
from gena.context import Context
from gena.biomodel import BioModel

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
        
    def test_reaction(self):
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
        
        print(rxn1)
        self.assertRaises(Exception, rxn1.add_product, comp4, 2)
        self.assertEqual(rxn1.to_str(), "(1.0) ATP_c + (1.0) Creatine_c <==(MyEnzyme)==> (1.0) ADP_n + (1.0) Phosphocreatine_n")
        
        rxn1.direction = "R"
        self.assertEqual(rxn1.to_str(), "(1.0) ATP_c + (1.0) Creatine_c ==(MyEnzyme)==> (1.0) ADP_n + (1.0) Phosphocreatine_n")
        print(rxn1)
        
        rxn1.direction = "L"
        self.assertEqual(rxn1.to_str(), "(1.0) ATP_c + (1.0) Creatine_c <==(MyEnzyme)== (1.0) ADP_n + (1.0) Phosphocreatine_n")
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
        
        print(net.to_json(prettify = True, stringify = True))

    def test_import(self):
        data_dir = settings.get_dir("gena:testdata_dir")
        file_path = os.path.join(data_dir, "small_net.json")
        
        with open(file_path) as f:
            data = json.load(f)
            net = Network.from_json(data)
        
        _json = net.dumps(stringify=True, prettify=True)
        print(_json)        
        print(net.to_json())
        
        self.assertEqual(len(net.compounds), 7)
        self.assertEqual(net.compounds["glc_D_e"].id, "glc_D_e")
        self.assertEqual(net.compounds["glc_D_e"].name, "D-Glucose")
        self.assertEqual(net.compounds["glc_D_e"].compartment, "e")
        self.assertEqual(net.compounds["atp_c"].id, "atp_c")
        self.assertEqual(net.compounds["atp_c"].name, "ATP C10H12N5O13P3")
        self.assertEqual(net.compounds["atp_c"].compartment, "c")
        self.assertEqual(len(net.reactions), 3)
        self.assertEqual(net.reactions["EX_glc_D_e"].to_str(), "(1.0) glc_D_e <==()==> *")
        self.assertEqual(net.reactions["GLNabc"].to_str(), "(1.0) atp_c + (1.0) gln_L_e <==()==> (1.0) adp_c + (1.0) gln_L_c")
        
        # export as table
        csv = net.to_csv()
        file_path = os.path.join(data_dir, "small_net.csv")
        with open(file_path, 'w') as f:
            f.write(csv)

        print(csv)

        S = net.create_stoichiometric_matrix()
        print("--> S_full")
        print(S)
        expected_S = DataFrame({
            'EX_glc_D_e': [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
            'GLNabc': [0.0, 1.0, -1.0, -1.0, 1.0, 0.0, 0.0],
            'biomass': [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        }, index=["glc_D_e", "gln_L_c", "gln_L_e", "atp_c", "adp_c", "adp_n", "biomass_b"])
        self.assertTrue(S.equals(expected_S))
        

        Si = net.create_intracell_stoichiometric_matrix()
        print("--> S_intra")
        print(Si)
        expected_Si = DataFrame({
            'EX_glc_D_e': [0.0, 0.0, 0.0, 0.0], 
            'GLNabc': [1.0, -1.0, 1.0, 0.0],
            'biomass': [0.0, 0.0, 0.0, 0.0],
        }, index=["gln_L_c", "atp_c", "adp_c", "adp_n"])
        self.assertTrue(Si.equals(expected_Si))
        
        Se = net.create_extracell_stoichiometric_matrix()
        print("--> S_extra")
        print(Se)
        expected_Se = DataFrame({
            'EX_glc_D_e': [-1.0, 0.0, 0.0], 
            'GLNabc': [0.0, -1.0, 0.0],
            'biomass': [-1.0, 0.0, 1.0],
        }, index=["glc_D_e", "gln_L_e", "biomass_b"])
        self.assertTrue(Se.equals(expected_Se))
