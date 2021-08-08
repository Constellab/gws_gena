
import os, json
import unittest
from pandas import DataFrame

from gws.unittest import GTest
from gws.settings import Settings
settings = Settings.retrieve()

from gena import Network, Compound, Reaction
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

    def test_network_import(self):
        GTest.print("Test Network Import")
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
        

        Si = net.create_steady_stoichiometric_matrix()
        print("--> S_intra")
        print(Si)
        expected_Si = DataFrame({
            'EX_glc_D_e': [0.0, 0.0, 0.0, 0.0], 
            'GLNabc': [1.0, -1.0, 1.0, 0.0],
            'biomass': [0.0, 0.0, 0.0, 0.0],
        }, index=["gln_L_c", "atp_c", "adp_c", "adp_n"])
        self.assertTrue(Si.equals(expected_Si))
        
        Se = net.create_non_steady_stoichiometric_matrix()
        print("--> S_extra")
        print(Se)
        expected_Se = DataFrame({
            'EX_glc_D_e': [-1.0, 0.0, 0.0], 
            'GLNabc': [0.0, -1.0, 0.0],
            'biomass': [-1.0, 0.0, 1.0],
        }, index=["glc_D_e", "gln_L_e", "biomass_b"])
        self.assertTrue(Se.equals(expected_Se))
