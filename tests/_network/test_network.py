
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import ConfigParams, File, GTest, Settings
from gws_gena import Compound, Network, NetworkImporter, Reaction, Twin
from pandas import DataFrame

settings = Settings.get_instance()


class TestNetwork(BaseTestCaseUsingFullBiotaDB):

    def test_network_import(self):
        self.print("Test Network Import")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "small_net")

        file_path = os.path.join(data_dir, "small_net.json")

        net = NetworkImporter.call(
            File(path=file_path),
            params={"skip_orphans": True}
        )

        json_data = net.dumps()
        print(json_data)
        print(net.loads(json_data))
        print(net.compounds)

        self.assertEqual(len(net.compounds), 6)
        self.assertEqual(net.compounds["glc_D_e"].id, "glc_D_e")
        self.assertEqual(net.compounds["glc_D_e"].name, "D-Glucose")
        self.assertEqual(net.compounds["glc_D_e"].compartment.id, "e")
        self.assertEqual(net.compounds["glc_D_e"].compartment.is_steady, False)
        self.assertEqual(net.compounds["atp_c"].id, "atp_c")
        self.assertEqual(net.compounds["atp_c"].name, "ATP C10H12N5O13P3")
        self.assertEqual(net.compounds["atp_c"].compartment.id, "c")
        self.assertEqual(len(net.reactions), 3)
        self.assertEqual(net.reactions["EX_glc_D_e"].to_str(), "(1.0) glc_D_e <==()==> *")
        self.assertEqual(
            net.reactions["GLNabc"].to_str(),
            "(1.0) atp_c + (1.0) gln_L_e <==()==> (1.0) adp_c + (1.0) gln_L_c")

        # export as table
        csv = net.to_csv()
        file_path = os.path.join(data_dir, "small_net.csv")
        with open(file_path, 'w', encoding="utf-8") as f:
            f.write(csv)

        print(csv)

        S = net.create_stoichiometric_matrix()
        print("--> S_full")
        print(S)
        expected_S = DataFrame({
            'EX_glc_D_e': [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'GLNabc': [0.0, 1.0, -1.0, -1.0, 1.0, 0.0],
            'biomass': [-1.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        }, index=["glc_D_e", "gln_L_c", "gln_L_e", "atp_c", "adp_c", "biomass_b"])

        # sort columns and index in the same order
        expected_S = expected_S.loc[S.index, :]
        expected_S = expected_S.loc[:, S.columns]

        self.assertTrue(S.equals(expected_S))

        Si = net.create_steady_stoichiometric_matrix()
        print("--> S_intra")
        print(Si)
        expected_Si = DataFrame({
            'EX_glc_D_e': [0.0, 0.0, 0.0],
            'GLNabc': [1.0, -1.0, 1.0],
            'biomass': [0.0, 0.0, 0.0],
        }, index=["gln_L_c", "atp_c", "adp_c"])

        expected_Si = expected_Si.loc[Si.index, :]
        expected_Si = expected_Si.loc[:, Si.columns]

        self.assertTrue(Si.equals(expected_Si))

        Se = net.create_non_steady_stoichiometric_matrix()
        print("--> S_extra")
        print(Se)
        expected_Se = DataFrame({
            'EX_glc_D_e': [-1.0, 0.0, 0.0],
            'GLNabc': [0.0, -1.0, 0.0],
            'biomass': [-1.0, 0.0, 1.0],
        }, index=["glc_D_e", "gln_L_e", "biomass_b"])

        expected_Se = expected_Se.loc[Se.index, :]
        expected_Se = expected_Se.loc[:, Se.columns]

        self.assertTrue(Se.equals(expected_Se))

    def test_network_import_bigg_file(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "ecoli")
        file_path = os.path.join(data_dir, "ecoli.json")
        # data_dir = os.path.join(data_dir, "ecoli/build")
        # file_path = os.path.join(data_dir, "ecoli_BL21_iECD_1391.json")

        # import 1
        net = NetworkImporter.call(
            File(path=file_path),
            params=ConfigParams({"skip_orphans": False})
        )
        self.print("ecoli successffuly imported - skip exchange reactions")
        self.assertEqual(len(net.compounds), 73)
        self.assertEqual(len(net.reactions), 75)

        # with open(os.path.join(data_dir, './build/', 'ecoli_dump.json'), 'w', encoding="utf-8") as fp:
        #     data = net.dumps()
        #     json.dump(data, fp, indent=4)

        # import 2
        net = NetworkImporter.call(
            File(path=file_path),
            params=ConfigParams({"skip_orphans": True})
        )
        self.print("ecoli successffuly imported - skip exchange reactions")
        self.assertEqual(len(net.compounds), 73)
        self.assertEqual(len(net.reactions), 75)
