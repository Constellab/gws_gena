from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import Settings
from gws_gena import Compartment, Compound, Network, Reaction
from gws_gena.network.exceptions.compound_exceptions import ProductDuplicateException
from gws_gena.network.typing.compound_typing import CompoundDict
from gws_gena.network.typing.reaction_typing import ReactionDict

settings = Settings.get_instance()


class TestNetwork(BaseTestCaseUsingFullBiotaDB):
    def test_reaction(self):
        self.print("Test Reaction")

        net = Network()

        rxn1 = Reaction(
            ReactionDict(
                id="my-reaction",
                name=None,
                direction=None,
                lower_bound=None,
                upper_bound=None,
                rhea_id=None,
                enzymes=None,
                layout=None,
                gene_reaction_rule=None,
                ec_numbers=None,
            )
        )
        net.add_reaction(rxn1)

        comp1 = Compound(
            CompoundDict(
                name="ATP",
                chebi_id="CHEBI:17234",
                compartment=Compartment.create_cytosol_compartment(),
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
        rxn1.add_substrate(comp1, -1, net)

        comp2 = Compound(
            CompoundDict(
                name="ADP",
                chebi_id="CHEBI:17235",
                compartment=Compartment.create_nucleus_compartment(),
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
        rxn1.add_product(comp2, +1, net)

        comp3 = Compound(
            CompoundDict(
                name="Creatine",
                chebi_id="CHEBI:17236",
                compartment=Compartment.create_cytosol_compartment(),
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
        rxn1.add_substrate(comp3, -1, net)

        comp4 = Compound(
            CompoundDict(
                name="Phosphocreatine",
                chebi_id="CHEBI:17237",
                compartment=Compartment.create_nucleus_compartment(),
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
        rxn1.add_product(comp4, 1, net)
        rxn1.enzymes = [
            {
                "ec_number": "MyEnzyme",
                "name": None,
                "tax": None,
                "pathways": None,
                "related_deprecated_enzyme": None,
            }
        ]

        self.print(rxn1.to_str())
        self.assertRaises(ProductDuplicateException, rxn1.add_product, comp4, 2)
        self.assertEqual(
            rxn1.to_str(),
            "(1.0) CHEBI:17234_cytosol + (1.0) CHEBI:17236_cytosol <==(MyEnzyme)==> (1.0) CHEBI:17235_nucleus + (1.0) CHEBI:17237_nucleus",
        )

        self.assertEqual(
            rxn1.to_str(show_names=True),
            "(1.0) ATP + (1.0) Creatine <==(MyEnzyme)==> (1.0) ADP + (1.0) Phosphocreatine",
        )

        rxn1.direction = "R"
        self.assertEqual(
            rxn1.to_str(),
            "(1.0) CHEBI:17234_cytosol + (1.0) CHEBI:17236_cytosol ==(MyEnzyme)==> (1.0) CHEBI:17235_nucleus + (1.0) CHEBI:17237_nucleus",
        )
        self.print(rxn1.to_str())

        rxn1.direction = "L"
        self.assertEqual(
            rxn1.to_str(),
            "(1.0) CHEBI:17234_cytosol + (1.0) CHEBI:17236_cytosol <==(MyEnzyme)== (1.0) CHEBI:17235_nucleus + (1.0) CHEBI:17237_nucleus",
        )
        self.print(rxn1.to_str())

        self.print("--->")
        rxns = Reaction.from_biota(rhea_id="RHEA:15133")
        for rxn in rxns:
            self.print(rxn.id)
            self.print(rxn.to_str())
            self.print(f"Mass/charge balance: {rxn.compute_mass_and_charge_balance()}")
            self.print(str(rxn.get_pathways()))

        self.print("--->")
        net = Network()
        rxns = Reaction.from_biota(
            ec_number="1.4.1.3", tax_id="42068", tax_search_method="bottom_up"
        )
        for rxn in rxns:
            net.add_reaction(rxn)
        for rxn in rxns:
            self.print(rxn.id)
            self.print(rxn.to_str())
            self.print(f"Mass/charge balance: {rxn.compute_mass_and_charge_balance()}")

        self.print("--->")
        sink_rxn = Reaction.create_sink_reaction(related_compound=comp4, network=net)
        self.print(sink_rxn.to_str())
