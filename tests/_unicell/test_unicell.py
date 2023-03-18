import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import Settings
from gws_gena import GapFinderHelper, Unicell


class TestUnicell(BaseTestCaseUsingFullBiotaDB):
    # def test_unicell(self):
    #     settings = Settings.get_instance()
    #     data_dir = settings.get_variable("gws_gena:testdata_dir")
    #     data_dir = os.path.join(data_dir, "./unicell/build")

    #     net = Unicell.create_network(refresh=False)

    #     print(f"number of reactions: {len(net.reactions)}")
    #     print(f"number of compounds: {len(net.compounds)}")

    #     helper = GapFinderHelper()
    #     table = helper.find_gaps(net)

    #     path = os.path.join(data_dir, "deadends.csv")
    #     with open(path, 'w', encoding="utf-8") as fp:
    #         table.to_csv(fp)

    def test_network_from_biota(self):
        df1 = Unicell.create_stoichiometric_matrix(refresh=False)
        df2 = Unicell.create_stoichiometric_matrix(tax_id="562", refresh=False)
        print(f"Size unicell: {df1.shape}")
        print(f"Size ecoli: {df2.shape}")

        self.assertTrue(df1.shape[0] > df2.shape[0])
        self.assertTrue(df1.shape[1] > df2.shape[1])

        dff2 = df1.loc[df2.index, df2.columns]
        self.assertTrue(dff2.equals(df2))
