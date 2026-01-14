from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_gena import Compartment, Compound
from gws_gena.network.typing.compound_typing import CompoundDict


class TestNetwork(BaseTestCaseUsingFullBiotaDB):
    def test_compound(self):
        compart = Compartment.from_biota(go_id=Compartment.CYTOSOL_GO_ID)
        comp1 = Compound(
            CompoundDict(
                name="gluc",
                compartment=compart,
                chebi_id="CHEBI:17234",
                id=None,
                charge=None,
                mass=None,
                monoisotopic_mass=None,
                formula=None,
                inchi=None,
                alt_chebi_ids=None,
                kegg_id=None,
                inchikey=None,
                layout=None,
            )
        )
        bc1 = comp1.get_related_biota_compound()
        if bc1 is None:
            raise ValueError("Biota compound not found")
        self.assertEqual(bc1.name, "glucose")
        self.assertEqual(bc1.kegg_id, "C00293")
        self.assertEqual(bc1.charge, 0)
        self.assertEqual(bc1.mass, 180.15588)
        self.assertEqual(bc1.monoisotopic_mass, 180.06339)

        comp2 = Compound(
            CompoundDict(
                name="gluc2",
                compartment=compart,
                id=None,
                charge=None,
                mass=None,
                monoisotopic_mass=None,
                formula=None,
                inchi=None,
                chebi_id=None,
                alt_chebi_ids=None,
                kegg_id=None,
                inchikey=None,
                layout=None,
            )
        )
        comp2.kegg_id = "C00293"
        bc2 = comp2.get_related_biota_compound()
        if bc2 is None:
            raise ValueError("Biota compound not found")
        self.assertEqual(bc2.name, "glucose")
        self.assertEqual(bc2.chebi_id, "CHEBI:17234")
        self.assertEqual(bc2.charge, 0)
        self.assertEqual(bc2.mass, 180.15588)
        self.assertEqual(bc2.monoisotopic_mass, 180.06339)

        comp3 = Compound.from_biota(kegg_id="C00293")
        self.assertEqual(comp3.monoisotopic_mass, 180.06339)
