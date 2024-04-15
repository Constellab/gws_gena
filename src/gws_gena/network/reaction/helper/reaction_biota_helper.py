
import re
from typing import List, Union

from gws_biota import Compound as BiotaCompound
from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import EnzymeOrtholog as BiotaEnzymeOrtholog
from gws_biota import Reaction as BiotaReaction
from gws_biota import Taxonomy as BiotaTaxo

from ....helper.base_helper import BaseHelper
from ...compartment.compartment import Compartment
from ...typing.compound_typing import CompoundDict
from ...typing.enzyme_typing import EnzymeDict
from ...typing.reaction_typing import ReactionDict

EQN_SPLIT_REGEXP = re.compile(r" <?=>? ")
OLIG_REGEXP = re.compile(r"\((n(\+\d)?)\)$")


class ReactionBiotaHelper(BaseHelper):
    """ ReactionBiotaHelper """

    def create_oligomer_if_required_and_add_to_reaction(
            self, biota_comps: List[BiotaCompound], stoich, rxn: 'Reaction', is_product: bool,
            compartment_go_id=None, alt_litteral_compound_name=None, oligomerization=None):
        """ Merge a list of compounds (oligomerisation) """

        from ...compound.compound import Compound

        if compartment_go_id is None:
            compartment_go_id = biota_comps[0].compartment.go_id

        names = [comp.name for comp in biota_comps]
        chebi_ids = [comp.chebi_id for comp in biota_comps]

        if oligomerization is not None:
            names.append(oligomerization)

        is_substrate = not is_product
        c = Compound(
            CompoundDict(
                chebi_id="_".join(chebi_ids),
                name="_".join(names),
                compartment=Compartment.from_biota(go_id=compartment_go_id)
            ))

        if is_substrate:
            comp_id_exists_in_products = (c.id in rxn.products)
            if comp_id_exists_in_products:
                # try to use the litteral name to uniquify the compound id
                if alt_litteral_compound_name:
                    c = Compound(CompoundDict(
                        chebi_id="_".join(chebi_ids) + "_" + alt_litteral_compound_name,
                        name=alt_litteral_compound_name,
                        compartment=c.compartment
                    ))
                else:
                    c = Compound(CompoundDict(
                        chebi_id="_".join(chebi_ids) + "_alt",
                        name=c.name + "_alt",
                        compartment=c.compartment
                    ))

        c.chebi_id = ",".join([comp_.chebi_id or "" for comp_ in biota_comps])
        c.kegg_id = ",".join([comp_.kegg_id or "" for comp_ in biota_comps])
        c.charge = sum(float(comp_.charge or 0.0) for comp_ in biota_comps)
        c.formula = ",".join([comp_.formula or "" for comp_ in biota_comps])
        c.mass = sum(float(comp_.mass or 0.0) for comp_ in biota_comps)
        c.monoisotopic_mass = sum(float(comp_.monoisotopic_mass or 0.0) for comp_ in biota_comps)
        c.layout = biota_comps[0].layout

        if is_product:
            rxn.add_product(c, stoich, update_if_exists=True)
        else:
            rxn.add_substrate(c, stoich, update_if_exists=True)

    def create_reaction_enzyme_dict_from_biota(
            self, enzymes: List[Union[BiotaEnzyme, BiotaEnzymeOrtholog]],
            load_taxonomy=True, load_pathway=True) -> EnzymeDict:
        """ create_reaction_enzyme_dict_from_biota """

        enzyme_list: List[EnzymeDict] = []

        found_ec_list = []
        for enzyme in enzymes:
            if enzyme:
                if enzyme.ec_number in found_ec_list:
                    # ensure unique ec_numbers
                    continue

                found_ec_list.append(enzyme.ec_number)
                enzyme_dict = EnzymeDict({
                    "name": enzyme.get_name(),
                    "tax": {},
                    "ec_number": enzyme.ec_number,
                    "pathways": {},
                    "related_deprecated_enzyme": {}
                })

                if load_taxonomy:
                    tax = BiotaTaxo.get_or_none(BiotaTaxo.tax_id == enzyme.tax_id)
                    if tax:
                        enzyme_dict["tax"][tax.rank] = {
                            "tax_id": tax.tax_id,
                            "name": tax.get_name()
                        }
                        for t in tax.ancestors:
                            enzyme_dict["tax"][t.rank] = {
                                "tax_id": t.tax_id,
                                "name": t.get_name()
                            }

                if enzyme.related_deprecated_enzyme:
                    enzyme_dict["related_deprecated_enzyme"] = {
                        "ec_number": enzyme.related_deprecated_enzyme.ec_number,
                        "reason": enzyme.related_deprecated_enzyme.data["reason"],
                    }

                if load_pathway:
                    pwy = enzyme.pathway
                    if pwy:
                        enzyme_dict["pathways"] = pwy.data

                enzyme_list.append(enzyme_dict)

        return enzyme_list

    def create_reaction_from_biota(self, rhea_rxn: BiotaReaction):
        """ Create a reaction """

        from ...reaction.reaction import Reaction

        enzyme_list: List[EnzymeDict] = self.create_reaction_enzyme_dict_from_biota(
            rhea_rxn.enzymes, load_taxonomy=False)

        rxn: Reaction = Reaction(
            ReactionDict(
                name=rhea_rxn.rhea_id,
                rhea_id=rhea_rxn.rhea_id,
                direction=rhea_rxn.direction,
                enzymes=enzyme_list
            ))
        rxn.layout = rhea_rxn.layout

        tab = re.split(EQN_SPLIT_REGEXP, rhea_rxn.data["definition"])
        substrate_definition = tab[0].split(" + ")
        product_definition = tab[1].split(" + ")

        tab = re.split(EQN_SPLIT_REGEXP, rhea_rxn.data["source_equation"])
        eqn_substrates = tab[0].split(" + ")
        eqn_products = tab[1].split(" + ")

        count = 0
        for sub in eqn_substrates:
            tab = sub.split(" ")
            if len(tab) == 2:
                stoich = tab[0].replace("n", "")
                if stoich == "":
                    stoich = 1.0
                chebi_ids = tab[1].split(",")
            else:
                stoich = 1.0
                chebi_ids = tab[0].split(",")

            biota_comps = []
            for id_ in chebi_ids:
                comp_tab = BiotaCompound.search_by_chebi_ids([id_])
                biota_comps.append(comp_tab[0])
                # try:
                #     comp_tab = BiotaCompound.search_by_chebi_ids([id_])
                #     biota_comps.append(comp_tab[0])
                # except Exception as err:
                #     print(rhea_rxn.rhea_id)
                #     raise Exception(f"{err}")

            litteral_comp_name = substrate_definition[count]
            if litteral_comp_name.endswith("(out)"):
                compartment_go_id = Compartment.EXTRACELL_SPACE_GO_ID
            else:
                compartment_go_id = Compartment.CYTOSOL_GO_ID

            tab = re.findall(OLIG_REGEXP, litteral_comp_name)
            oligo = tab[0][0] if len(tab) else None
            self.create_oligomer_if_required_and_add_to_reaction(
                biota_comps,
                stoich,
                rxn,
                is_product=True,
                compartment_go_id=compartment_go_id,
                alt_litteral_compound_name=None,
                oligomerization=oligo
            )
            count += 1

        count = 0
        for prod in eqn_products:
            tab = prod.split(" ")
            if len(tab) == 2:
                stoich = tab[0]
                chebi_ids = tab[1].split(",")
            else:
                stoich = 1
                chebi_ids = tab[0].split(",")

            biota_comps = []
            for id_ in chebi_ids:
                comp_tab = BiotaCompound.search_by_chebi_ids([id_])
                biota_comps.append(comp_tab[0])
                # try:
                #     comp_tab = BiotaCompound.search_by_chebi_ids([id_])
                #     biota_comps.append(comp_tab[0])
                # except Exception as err:
                #     # search for alternative chebi_id
                #     print(rhea_rxn.rhea_id)
                #     raise Exception(f"{err}")

            litteral_comp_name = product_definition[count]
            if litteral_comp_name.endswith("(out)"):
                compartment_go_id = Compartment.EXTRACELL_SPACE_GO_ID
            else:
                compartment_go_id = Compartment.CYTOSOL_GO_ID

            tab = re.findall(OLIG_REGEXP, litteral_comp_name)
            oligo = tab[0][0] if len(tab) else None
            self.create_oligomer_if_required_and_add_to_reaction(
                biota_comps,
                stoich,
                rxn=rxn,
                is_product=False,
                compartment_go_id=compartment_go_id,
                alt_litteral_compound_name=litteral_comp_name,
                oligomerization=oligo
            )
            count += 1

        return rxn
