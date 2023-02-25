
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import Settings
from gws_gena import Unicell


class TestUnicell(BaseTestCaseUsingFullBiotaDB):
    def test_network_from_biota(self):
        df = Unicell.create_stoichiometric_matrix(refresh=False)
        print(df.shape)
