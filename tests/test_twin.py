
import os, json
import unittest

from gws.settings import Settings
settings = Settings.retrieve()
settings.use_prod_biota_db(True)

from gena.twin import Compound, Reaction, Twin
from gena.context import Context
from biota.db.compound import Compound as BiotaCompound


class TestTwin(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Twin.drop_table()
        Twin.create_table()
        pass

    @classmethod
    def tearDownClass(cls):
        settings.use_prod_biota_db(False)
        pass
    
    def test_compound(self):
        t = Twin()        
        comp1 = Compound(id=1, twin=t, chebi_id="CHEBI:17234", compartment=Compound.COMPARTMENT_CYTOSOL)
        
        bc1 = comp1.get_related_biota_compound()
        self.assertEqual(bc1.name, "glucose")
        self.assertEqual(bc1.kegg_id, "C00293")
        self.assertEqual(bc1.charge, 0)
        self.assertEqual(bc1.mass, 180.15588)
        self.assertEqual(bc1.monoisotopic_mass, 180.06339)
        
        comp2 = Compound(compartment=Compound.COMPARTMENT_CYTOSOL)
        t.add_compound(comp2)
        comp2.kegg_id = "C00293"
        bc2 = comp2.get_related_biota_compound()
        self.assertEqual(bc2.name, "glucose")
        self.assertEqual(bc2.chebi_id, "CHEBI:17234")
        self.assertEqual(bc2.charge, 0)
        self.assertEqual(bc2.mass, 180.15588)
        self.assertEqual(bc2.monoisotopic_mass, 180.06339)
        
        comp3 = Compound.from_extern(kegg_id="C00293")
        self.assertEqual(comp3.monoisotopic_mass, 180.06339)
        
    def test_reaction(self):
        t = Twin()
  
        rxn1 = Reaction()
        t.add_reaction(rxn1)
        
        comp1 = Compound(id="ATP[c]", chebi_id="CHEBI:17234", compartment=Compound.COMPARTMENT_CYTOSOL)
        rxn1.add_substrate(comp1, -1)
        
        comp2 = Compound(id="ADP[n]", chebi_id="CHEBI:17235", compartment=Compound.COMPARTMENT_NUCLEUS)
        rxn1.add_product(comp2, +1)
        
        comp3 = Compound(id="Creatine[c]", chebi_id="CHEBI:17236", compartment=Compound.COMPARTMENT_CYTOSOL)
        rxn1.add_substrate(comp3, -1)
        
        comp4 = Compound(id="Phosphocreatine[n]", chebi_id="CHEBI:17237", compartment=Compound.COMPARTMENT_NUCLEUS)
        rxn1.add_product(comp4, 1)
        
        print(rxn1)
        self.assertRaises(Exception, rxn1.add_product, comp4, 2)
        self.assertEqual(str(rxn1), "(1) ATP[c] + (1) Creatine[c] <=> (1) ADP[n] + (1) Phosphocreatine[n]")
        
        rxn1.direction = "R"
        self.assertEqual(str(rxn1), "(1) ATP[c] + (1) Creatine[c] => (1) ADP[n] + (1) Phosphocreatine[n]")
        print(rxn1)
        
        rxn1.direction = "L"
        self.assertEqual(str(rxn1), "(1) ATP[c] + (1) Creatine[c] <= (1) ADP[n] + (1) Phosphocreatine[n]")
        print(rxn1)
    
    def test_import(self):
        data_dir = settings.get_dir("gena:testdata_dir")
        file_path = os.path.join(data_dir, "small.json")
        
        with open(file_path) as f:
            data = json.load(f)
            tw = Twin.from_json(data)
        
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
        
        self.assertEqual(str(tw.reactions["EX_glc__D_e"]), "(1.0) glc__D_e <=> *")
        self.assertEqual(str(tw.reactions["GLNabc"]), "(1.0) atp_c + (1.0) gln__L_e <=> (1.0) adp_c + (1.0) gln__L_c")
    
    def test_import_with_context(self):
        
        data_dir = settings.get_dir("gena:testdata_dir")
        
        file_path = os.path.join(data_dir, "small.json")
        with open(file_path) as f:
            data = json.load(f)
            tw = Twin.from_json(data)
        
        file_path = os.path.join(data_dir, "toy_phenotype.json")
        with open(file_path) as f:
            data = json.load(f)
            ctx = Context.from_json(data)
        
        tw.add_context(ctx)
        
        print("----------------------")
        print(tw.as_json(expand_context=True))