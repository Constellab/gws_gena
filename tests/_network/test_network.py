
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
            params={'skip_orphans': True}
        )

        json_data = net.dumps()
        print(json_data)
        print(net.loads(json_data))
        print(net.compounds)

        self.assertEqual(len(net.compounds), 7)
        self.assertEqual(net.compounds["glc_D_e"].id, "glc_D_e")
        self.assertEqual(net.compounds["glc_D_e"].name, "D-Glucose")
        self.assertEqual(net.compounds["glc_D_e"].compartment.id, "e")
        self.assertEqual(net.compounds["glc_D_e"].compartment.is_steady, False)
        self.assertEqual(net.compounds["atp_c"].id, "atp_c")
        self.assertEqual(net.compounds["atp_c"].name, "ATP C10H12N5O13P3")
        self.assertEqual(net.compounds["atp_c"].compartment.id, "c")
        self.assertEqual(len(net.reactions), 3)
        self.assertEqual(
            net.reactions["GLNabc"].to_str(),
            "(1.0) atp_c + (1.0) gln_L_e <==()==> (1.0) adp_c + (1.0) gln_L_c")

        # export as table
        csv = net.to_csv()
        file_path = os.path.join(data_dir, "small_net.csv")
        with open(file_path, 'w', encoding="utf-8") as f:
            f.write(csv)

        print(csv)

        stoich = net.create_stoichiometric_matrix()
        print("--> S_full")
        print(stoich)
        expected_s = DataFrame({
            'glc_D_transport': [-1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'GLNabc': [0.0, 0.0, 1.0, -1.0, 1.0, -1.0, 0.0],
            'biomass': [0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        }, index=["glc_D_e", "glc_D_c", "adp_c", "atp_c", "gln_L_c", "gln_L_e", "biomass_b"])

        # sort columns and index in the same order
        expected_s = expected_s.loc[stoich.index, :]
        expected_s = expected_s.loc[:, stoich.columns]

        self.assertTrue(stoich.equals(expected_s))

        stoich_in = net.create_steady_stoichiometric_matrix()
        print("--> S_intra")
        print(stoich_in)
        expected_s_in = DataFrame({
            'glc_D_transport': [1.0, 0.0, 0.0, 0.0],
            'GLNabc': [0.0, 1.0, -1.0, 1.0],
            'biomass': [-1.0, 0.0, 0.0, 0.0],
        }, index=["glc_D_c", "adp_c", "atp_c", "gln_L_c"])

        expected_s_in = expected_s_in.loc[stoich_in.index, :]
        expected_s_in = expected_s_in.loc[:, stoich_in.columns]

        self.assertTrue(stoich_in.equals(expected_s_in))

        stoich_ex = net.create_non_steady_stoichiometric_matrix()
        print("--> S_extra")
        print(stoich_ex)
        expected_s_ex = DataFrame({
            'glc_D_transport': [-1.0, 0.0, 0.0],
            'GLNabc': [0.0, -1.0, 0.0],
            'biomass': [0.0, 0.0, 1.0],
        }, index=["glc_D_e", "gln_L_e", "biomass_b"])

        expected_s_ex = expected_s_ex.loc[stoich_ex.index, :]
        expected_s_ex = expected_s_ex.loc[:, stoich_ex.columns]

        self.assertTrue(stoich_ex.equals(expected_s_ex))

    def test_network_import_bigg_file(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "ecoli")
        file_path = os.path.join(data_dir, "ecoli.json")

        net = NetworkImporter.call(
            File(path=file_path),
            params={}
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
            params={}
        )
        self.print("ecoli successffuly imported - skip exchange reactions")
        self.assertEqual(len(net.compounds), 73)
        self.assertEqual(len(net.reactions), 75)
