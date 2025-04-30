
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, Settings
from gws_gena.network.network_task.network_importer_v2 import NetworkImporterV2
from pandas import DataFrame
from gws_biota import Compartment

settings = Settings.get_instance()


class TestNetwork(BaseTestCaseUsingFullBiotaDB):

    def test_network_import(self):
        self.print("Test Network Import")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "small_net")

        file_path = os.path.join(data_dir, "small_net_v2.json")

        net = NetworkImporterV2.call(File(path=file_path),
            params={'skip_orphans': True})

        """json_data = net.dumps()
        print(json_data)
        print(net.loads(json_data))
        print(net.compounds)"""

        self.assertEqual(len(net.get_metabolites()), 8)
        self.assertEqual(net.get_metabolite_by_id_and_check("glc_D_e").id, "glc_D_e")
        self.assertEqual(net.get_metabolite_by_id_and_check("glc_D_e").name, "D-Glucose")
        self.assertEqual(net.get_metabolite_by_id_and_check("glc_D_e").compartment, "e")
        self.assertEqual(Compartment.get_by_bigg_id_or_go_id_or_none(net.get_metabolite_by_id_and_check("glc_D_e").compartment).is_steady, True)
        self.assertEqual(net.get_metabolite_by_id_and_check("atp_c").id, "atp_c")
        self.assertEqual(net.get_metabolite_by_id_and_check("atp_c").name, "ATP C10H12N5O13P3")
        self.assertEqual(net.get_metabolite_by_id_and_check("atp_c").compartment, "c")
        self.assertEqual(len(net.get_reactions()), 3)
        self.assertEqual(net.get_reaction_by_id_and_check('biomass').gene_reaction_rule,'')
        #self.assertEqual(net.get_reaction_by_id_and_check("GLNabc").to_str(),"(1.0) atp_c + (1.0) gln_L_e <==()==> (1.0) adp_c + (1.0) gln_L_c")

        # export as table
        """csv = net.to_csv()
        file_path = os.path.join(data_dir, "small_net.csv")
        with open(file_path, 'w', encoding="utf-8") as f:
            f.write(csv)"""

        stoich = net.create_stoichiometric_matrix()
        print("--> S_full")
        print(stoich)
        expected_s = DataFrame({
            'glc_D_transport': [-1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'GLNabc': [0.0, 0.0, 1.0, -1.0, 1.0, -1.0, 0.0, 0.0],
            'biomass': [0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        }, index=["glc_D_e", "glc_D_c", "adp_c", "atp_c", "gln_L_c", "gln_L_e", "biomass_b", "adp_n"])

        # sort columns and index in the same order
        expected_s = expected_s.loc[stoich.index, :] #TODO voir si il faut garder les métabolites venant du compartiment nucleus
        expected_s = expected_s.loc[:, stoich.columns]

        self.assertTrue(stoich.equals(expected_s))

        stoich_in = net.create_steady_stoichiometric_matrix()
        print("--> S_intra")
        print(stoich_in)
        expected_s_in = DataFrame({
            'glc_D_transport': [-1.0,1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'GLNabc': [0.0, 0.0, 1.0, -1.0, 1.0, -1.0, 0.0],
            'biomass': [0.0,-1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        }, index=["glc_D_e", "glc_D_c", "adp_c", "atp_c", "gln_L_c", "gln_L_e", "adp_n"])

        expected_s_in = expected_s_in.loc[stoich_in.index, :]
        expected_s_in = expected_s_in.loc[:, stoich_in.columns]

        self.assertTrue(stoich_in.equals(expected_s_in))

        stoich_ex = net.create_non_steady_stoichiometric_matrix()
        print("--> S_extra")
        print(stoich_ex)
        expected_s_ex = DataFrame({
            'glc_D_transport': [0.0],
            'GLNabc': [0.0],
            'biomass': [1.0],
        }, index=["biomass_b"])

        expected_s_ex = expected_s_ex.loc[stoich_ex.index, :]
        expected_s_ex = expected_s_ex.loc[:, stoich_ex.columns]

        self.assertTrue(stoich_ex.equals(expected_s_ex))

    def test_network_import_bigg_file(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        data_dir = os.path.join(data_dir, "ecoli")
        file_path = os.path.join(data_dir, "ecoli.json")

        net = NetworkImporterV2.call(
            File(path=file_path)
        )

        self.print("ecoli successffuly imported")
        self.assertEqual(len(net.get_metabolites()), 72)
        self.assertEqual(len(net.get_reactions()), 95)
        self.assertEqual(net.get_reaction_by_id_and_check("EX_o2_e").id, "EX_o2_e")

        # with open(os.path.join(data_dir, './build/', 'ecoli_dump.json'), 'w', encoding="utf-8") as fp:
        #     data = net.dumps()
        #     json.dump(data, fp, indent=4)

        # import 2
        net = NetworkImporterV2.call(
            File(path=file_path)
        )
        self.print("ecoli successfully imported")
        self.assertEqual(len(net.get_metabolites()), 72)
        self.assertEqual(len(net.get_reactions()), 95)
