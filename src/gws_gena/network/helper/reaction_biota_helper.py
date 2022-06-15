# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import re
from typing import List, Union

from gws_biota import Compound as BiotaCompound
from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import EnzymeOrtholog as BiotaEnzymeOrtholog
from gws_biota import Reaction as BiotaReaction
from gws_biota import Taxonomy as BiotaTaxo

from ..typing.reaction_enzyme_typing import EnzymeDict

EQN_SPLIT_REGEXP = re.compile(r" <?=>? ")
OLIG_REGEXP = re.compile(r"\((n(\+\d)?)\)$")


class ReactionBiotaHelper:
    """ ReactionBiotaHelper """

    @classmethod
    def merge_compounds_and_add_to_reaction(
            cls, comps: List[BiotaCompound], stoich, rxn: 'Reaction', is_product: bool,
            compartment=None, alt_litteral_comppound_name=None, oligomerization=None):
        """ Merge a list of compounds (oligomerisation) """

        from ..compound import Compound

        if compartment is None:
            compartment = comps[0].compartment

        names = []
        for comp in comps:
            names.append(comp.name)

        if oligomerization is not None:
            names.append(oligomerization)

        is_substrate = not is_product
        c = Compound(name=",".join(names), compartment=compartment)
        if is_substrate:
            comp_id_exists_in_products = (c.id in rxn.products)
            if comp_id_exists_in_products and alt_litteral_comppound_name:
                # use the litteral name to uniquify the compound id
                c = Compound(name=alt_litteral_comppound_name, compartment=compartment)

        c.chebi_id = ",".join([comp_.chebi_id or "" for comp_ in comps])
        c.kegg_id = ",".join([comp_.kegg_id or "" for comp_ in comps])
        c.charge = str(sum([float(comp_.charge or 0.0) for comp_ in comps]))
        c.formula = ",".join([comp_.formula or "" for comp_ in comps])
        c.mass = str(sum([float(comp_.mass or 0.0) for comp_ in comps]))
        c.monoisotopic_mass = str(sum([float(comp_.monoisotopic_mass or 0.0) for comp_ in comps]))
        c.layout = comps[0].layout

        if is_product:
            rxn.add_product(c, stoich)
        else:
            rxn.add_substrate(c, stoich)
    # return c

    @classmethod
    def create_reaction_enzyme_dict_from_biota(
            cls, enzyme: Union[BiotaEnzyme, BiotaEnzymeOrtholog], load_taxonomy=True, load_pathway=True) -> EnzymeDict:
        """ create_reaction_enzyme_dict_from_biota """
        if enzyme:
            e = {
                "name": enzyme.get_name(),
                "ec_number": enzyme.ec_number,
            }
            e["tax"] = {}
            if isinstance(enzyme, BiotaEnzyme):
                if load_taxonomy:
                    tax = BiotaTaxo.get_or_none(BiotaTaxo.tax_id == enzyme.tax_id)
                    if tax:
                        e["tax"][tax.rank] = {
                            "tax_id": tax.tax_id,
                            "name": tax.get_name()
                        }
                        for t in tax.ancestors:
                            e["tax"][t.rank] = {
                                "tax_id": t.tax_id,
                                "name": t.get_name()
                            }

                if enzyme.related_deprecated_enzyme:
                    e["related_deprecated_enzyme"] = {
                        "ec_number": enzyme.related_deprecated_enzyme.ec_number,
                        "reason": enzyme.related_deprecated_enzyme.reason,
                    }

            e["pathways"] = {}
            if load_pathway:
                pwy = enzyme.pathway
                if pwy:
                    e["pathways"] = pwy.data
        else:
            e = {}

        return e

    @classmethod
    def create_reaction_from_biota(cls, rhea_rxn: BiotaReaction, enzyme: BiotaEnzyme):
        """ Create a reaction """

        from ..compartment import Compartment
        from ..reaction import Reaction

        e: EnzymeDict = cls.create_reaction_enzyme_dict_from_biota(enzyme)

        rxn: Reaction = Reaction(name=rhea_rxn.rhea_id+"_"+enzyme.ec_number,
                                 rhea_id=rhea_rxn.rhea_id,
                                 direction=rhea_rxn.direction,
                                 enzyme=e)
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
                biota_comps.append(BiotaCompound.get(BiotaCompound.chebi_id == id_))

            litteral_comp_name = substrate_definition[count]
            if litteral_comp_name.endswith("(out)"):
                compartment = Compartment.EXTRACELLULAR_SPACE
            else:
                compartment = Compartment.CYTOSOL

            tab = re.findall(OLIG_REGEXP, litteral_comp_name)
            oligo = tab[0][0] if len(tab) else None
            cls.merge_compounds_and_add_to_reaction(
                biota_comps,
                stoich,
                rxn,
                is_product=True,
                compartment=compartment,
                alt_litteral_comppound_name=None,
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
                biota_comps.append(BiotaCompound.get(BiotaCompound.chebi_id == id_))

            litteral_comp_name = product_definition[count]
            if litteral_comp_name.endswith("(out)"):
                compartment = Compartment.EXTRACELLULAR_SPACE
            else:
                compartment = Compartment.CYTOSOL

            tab = re.findall(OLIG_REGEXP, litteral_comp_name)
            oligo = tab[0][0] if len(tab) else None
            cls.merge_compounds_and_add_to_reaction(
                biota_comps,
                stoich,
                rxn=rxn,
                is_product=False,
                compartment=compartment,
                alt_litteral_comppound_name=litteral_comp_name,
                oligomerization=oligo
            )
            count += 1

        return rxn
