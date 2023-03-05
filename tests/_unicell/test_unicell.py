
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_gena import Unicell


class TestUnicell(BaseTestCaseUsingFullBiotaDB):
    def test_network_from_biota(self):
        df1 = Unicell.create_stoichiometric_matrix(refresh=False)
        df2 = Unicell.create_stoichiometric_matrix(tax_id="562", refresh=False)
        print(f"Size unicell: {df1.shape}")
        print(f"Size ecoli: {df2.shape}")

        self.assertTrue(df1.shape[0] > df2.shape[0])
        self.assertTrue(df1.shape[1] > df2.shape[1])

        dff2 = df1.loc[df2.index, df2.columns]
        self.assertTrue(dff2.equals(df2))
