
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import GTest, Settings
from gws_gena import Compartment, Compound, Context, Network, Reaction, Twin
from pandas import DataFrame

settings = Settings.retrieve()


class TestNetwork(BaseTestCaseUsingFullBiotaDB):

    def test_reaction(self):
        self.print("Test Reaction")

        net = Network()

        rxn1 = Reaction(dict(id="my-reaction"))
        net.add_reaction(rxn1)

        comp1 = Compound(dict(name="ATP", chebi_id="CHEBI:17234", compartment=Compartment.create_cytosol_compartment()))
        rxn1.add_substrate(comp1, -1, net)

        comp2 = Compound(dict(name="ADP", chebi_id="CHEBI:17235", compartment=Compartment.create_nucleus_compartment()))
        rxn1.add_product(comp2, +1, net)

        comp3 = Compound(dict(name="Creatine", chebi_id="CHEBI:17236",
                         compartment=Compartment.create_cytosol_compartment()))
        rxn1.add_substrate(comp3, -1, net)

        comp4 = Compound(dict(name="Phosphocreatine", chebi_id="CHEBI:17237",
                         compartment=Compartment.create_nucleus_compartment()))
        rxn1.add_product(comp4, 1, net)
        rxn1.enzyme = {"ec_number": "MyEnzyme"}

        print(rxn1.to_str())
        self.assertRaises(Exception, rxn1.add_product, comp4, 2)
        self.assertEqual(
            rxn1.to_str(),
            "(1.0) ATP_cytosol + (1.0) Creatine_cytosol <==(MyEnzyme)==> (1.0) ADP_nucleus + (1.0) Phosphocreatine_nucleus")

        rxn1.direction = "R"
        self.assertEqual(
            rxn1.to_str(),
            "(1.0) ATP_cytosol + (1.0) Creatine_cytosol ==(MyEnzyme)==> (1.0) ADP_nucleus + (1.0) Phosphocreatine_nucleus")
        print(rxn1.to_str())

        rxn1.direction = "L"
        self.assertEqual(
            rxn1.to_str(),
            "(1.0) ATP_cytosol + (1.0) Creatine_cytosol <==(MyEnzyme)== (1.0) ADP_nucleus + (1.0) Phosphocreatine_nucleus")
        print(rxn1.to_str())

        print("--->")
        rxns = Reaction.from_biota(rhea_id="RHEA:15133")
        for rxn in rxns:
            print(rxn.id)
            print(rxn.to_str())
            print(f"Mass/charge balance: {rxn.compute_mass_and_charge_balance()}")
            print(rxn.get_pathways())

        print("--->")
        net = Network()
        rxns = Reaction.from_biota(ec_number="1.4.1.3", tax_id="42068", tax_search_method="bottom_up")
        for rxn in rxns:
            net.add_reaction(rxn)
        for rxn in rxns:
            print(rxn.id)
            print(rxn.to_str())
            print(f"Mass/charge balance: {rxn.compute_mass_and_charge_balance()}")

        print("--->")
        sink_rxn = Reaction.create_sink_reaction(related_compound=comp4, network=net)
        print(sink_rxn.to_str())
