# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
import random
from typing import List

from gws_biota import Cofactor as BiotaCofactor
from gws_biota import Compound as BiotaCompound
from gws_biota import CompoundClusterDict as BiotaCompoundClusterDict
from gws_biota import CompoundLayout as BiotaCompoundLayout
from gws_biota import CompoundLayoutDict as BiotaCompoundLayoutDict
from gws_biota import Residue as BiotaResidue
from gws_core import BadRequestException

from ..compartment.compartment import Compartment
from ..exceptions.compound_exceptions import CompoundNotFoundException
from ..helper.slugify_helper import SlugifyHelper
from ..typing.compound_typing import CompoundDict


class Compound:
    """
    Class that represents a compound of a network.

    Networks' compounds are proxy of biota compounds (i.e. Chebi compounds).
    They a used to build reconstructed digital twins.

    :property id: The id of the compound
    :type id: `str`
    :property name: The name of the compound
    :type name: `str`
    :property charge: The charge of the compound
    :type charge: `str`
    :property mass: The mass of the compound
    :type mass: `str`
    :property monoisotopic_mass: The monoisotopic mass of the compound
    :type monoisotopic_mass: `str`
    :property formula: The formula of the compound
    :type formula: `str`
    :property inchi: The inchi of the compound
    :type inchi: `str`
    :property compartment: The compartment of the compound
    :type compartment: `str`
    :property compartment: The compartment of the compound
    :type compartment: `str`
    :property chebi_id: The corresponding ChEBI id of the compound
    :type chebi_id: `str`
    :property kegg_id: The corresponding Kegg id of the compound
    :type kegg_id: `str`
    """

    DELIMITER = "_"

    DEFAULT_TYPE = "default"
    COFACTOR_TYPE = "cofactor"
    RESIDUE_TYPE = "residue"

    id: str = ""
    name: str = ""
    charge: float = None
    mass: float = None
    monoisotopic_mass: float = None
    formula: str = ""
    inchi: str = ""
    compartment: Compartment = None
    chebi_id: str = ""
    alt_chebi_ids: List = None
    kegg_id: str = ""
    inchikey: str = ""
    layout: BiotaCompoundLayoutDict = None

    def __init__(self, dict_: CompoundDict = None):
        if dict_ is None:
            dict_ = {}
        for key, val in dict_.items():
            setattr(self, key, val)

        if self.chebi_id is None:
            self.chebi_id = ""
        if self.inchikey is None:
            self.inchikey = ""

        if not isinstance(self.compartment, Compartment):
            raise BadRequestException("The compartment is not valid")
        if not isinstance(self.chebi_id, str):
            raise BadRequestException("The chebi_id must be a string")
        if not isinstance(self.inchikey, str):
            raise BadRequestException("The inchikey must be a string")

        if self.id:
            self.id = SlugifyHelper.slugify_id(self.id)
        else:
            if not self.name:
                if self.chebi_id:
                    c = BiotaCompound.get_or_none(BiotaCompound.chebi_id == self.chebi_id)
                    if c is not None:
                        self.name = c.get_name()
                    else:
                        self.name = self.chebi_id
                else:
                    raise CompoundNotFoundException("The chebi_id is not valid")

            self.id = SlugifyHelper.slugify_id(
                self.name + self.DELIMITER + self.compartment.name
            )

        if not self.name:
            self.name = self.id

        if self.alt_chebi_ids is None:
            self.alt_chebi_ids = []

        if self.layout is None:
            # refresh layout
            self.layout = BiotaCompoundLayout.get_layout_by_chebi_id(
                synonym_chebi_ids=self.chebi_id)

        if self.is_biomass():
            self.append_biomass_layout(is_biomass=True)

    # -- A --

    def append_biomass_layout(self, is_biomass=False):
        """ Append biomass layout """
        if self.is_cofactor():
            return

        if self.layout is None:
            # check attribute for retro-compatiblity
            # TODO: remove on next major
            self.layout = BiotaCompoundLayout.get_empty_layout()

        if "clusters" not in self.layout:
            self.layout["clusters"] = {}

        bioass_cluster = BiotaCompoundLayout.get_biomass_layout(is_biomass=is_biomass)["clusters"]
        self.layout["clusters"].update(bioass_cluster)

    # -- C --

    def copy(self) -> 'Compound':
        """ Create a copy of the compound """
        c = Compound(
            CompoundDict(
                id=self.id,
                name=self.name,
                compartment=self.compartment
            ))
        c.charge = self.charge
        c.mass = self.mass
        c.monoisotopic_mass = self.monoisotopic_mass
        c.formula = self.formula
        c.inchi = self.inchi
        c.chebi_id = self.chebi_id
        c.alt_chebi_ids = copy.deepcopy(self.alt_chebi_ids)
        c.kegg_id = self.kegg_id
        c.inchikey = self.inchikey
        if self.layout is None:
            # check attribute for retro-compatiblity
            # TODO: remove on next major
            self.layout = {}

        c.layout = self.layout
        return c

    @ classmethod
    def create_sink_compound(cls, related_compound: 'Compound') -> 'Compound':
        """ Create a sink compound """
        compart = related_compound.compartment
        if compart.is_sink():
            raise BadRequestException("Cannot add a sink reaction to another sink reaction")

        return Compound(
            CompoundDict(
                id=None,
                name=related_compound.name,
                compartment=Compartment.create_sink_compartment(),
                chebi_id=related_compound.chebi_id,
                inchikey=related_compound.inchikey,
            ))

    # -- F --

    # @classmethod
    # def from_bulk_biota(cls, chebi_ids: List = None, compartment="") -> dict:
    #     """
    #     Create a a list of compounds from a list of chebi_ids

    #     Faster than iterating with method `from_biota()`
    #     """

    #     Q = BiotaCompound.select().where(BiotaCompound.chebi_id.in_(chebi_ids))
    #     list_of_comps = {}
    #     for biota_compound in Q:
    #         c = Compound(
    #             id=None,
    #             name=biota_compound.name,
    #             compartment=compartment,
    #             chebi_id=biota_compound.chebi_id,
    #             kegg_id=biota_compound.kegg_id,
    #             inchikey=biota_compound.inchikey,
    #             charge=biota_compound.charge,
    #             formula=biota_compound.formula,
    #             mass=biota_compound.mass,
    #             monoisotopic_mass=biota_compound.monoisotopic_mass,
    #         )
    #         list_of_comps[c.chebi_id].append(c)
    #     return list_of_comps

    @ classmethod
    def from_biota(cls, *, id=None, name="", biota_compound=None, chebi_id="", kegg_id="", inchikey="",
                   compartment_go_id="") -> 'Compound':
        """
        Create a network compound from a ChEBI of Kegg id

        :param biota_compound: The biota compound to use. If not provided, the chebi_id or keeg_id are used to fetch the corresponding compound from the biota db.
        :type biota_compound: `biota.compound.Compound`
        :param chebi_id: The ChEBI id
        :type chebi_id: `str`
        :param kegg_id: The Kegg id
        :type kegg_id: `str`
        :return: The compound
        :rtype: `gena.compound.Compound`
        """

        if biota_compound is None and chebi_id:
            if isinstance(chebi_id, (float, int)):
                chebi_id = "CHEBI:"+str(chebi_id)
            biota_compound = BiotaCompound.get_or_none(BiotaCompound.chebi_id == chebi_id)
        if biota_compound is None and inchikey:
            biota_compound = BiotaCompound.get_or_none(BiotaCompound.inchikey == inchikey)
        if biota_compound is None and kegg_id:
            biota_compound = BiotaCompound.get_or_none(BiotaCompound.kegg_id == kegg_id)

        if biota_compound is None:
            raise CompoundNotFoundException(
                f"Cannot find compound (chebi_id={chebi_id})")

        if not compartment_go_id:
            compart = Compartment.create_cytosol_compartment()
        else:
            compart = Compartment.from_biota(go_id=compartment_go_id)
        if not name:
            name = biota_compound.name

        c = Compound(
            CompoundDict(
                id=id,
                name=name,
                compartment=compart,
                chebi_id=biota_compound.chebi_id,
                kegg_id=biota_compound.kegg_id,
                inchikey=biota_compound.inchikey,
                charge=biota_compound.charge,
                formula=biota_compound.formula,
                mass=biota_compound.mass,
                monoisotopic_mass=biota_compound.monoisotopic_mass,
            ))

        return c

    # -- G --

    def get_layout(self, refresh: bool = False) -> int:
        """ Get compound layout """

        def rnd_offset():
            """ Random offset """
            rnd_num = random.uniform(0, 1)
            return -1 if rnd_num >= 0.5 else 1

        if self.layout is None:
            return BiotaCompoundLayout.get_empty_layout()
        else:
            if refresh:
                if self.chebi_id:
                    layout: BiotaCompoundLayoutDict = BiotaCompoundLayout.get_layout_by_chebi_id(
                        synonym_chebi_ids=self.chebi_id)
                    layout = copy.deepcopy(layout)

                    if not self.compartment.is_cytosol() and not self.compartment.is_biomass():
                        for clust in layout["clusters"].values():
                            if clust.get("x"):
                                clust["x"] = clust["x"] + 100*rnd_offset()
                                clust["y"] = clust["y"] + 100*rnd_offset()
                else:
                    layout = self.layout
            else:
                layout = self.layout

            return layout

    def get_level(self) -> int:
        """ Get compound level """
        if self.layout is None:
            # check attribute for retro-compatiblity
            # TODO: remove on next major
            return 2

        return self.layout.get("level", 2)

    def get_related_biota_compound(self):
        """
        Get the biota compound that is related to this network compound

        :return: The biota compound corresponding to the chebi of kegg id. Returns `None` is no biota coumpund is found
        :rtype: `bioa.compound.Compound`, `None`
        """

        if self.chebi_id:
            return BiotaCompound.get_or_none(BiotaCompound.chebi_id == self.chebi_id)
        elif self.kegg_id:
            return BiotaCompound.get_or_none(BiotaCompound.kegg_id == self.kegg_id)
        return None

    def get_related_biota_reactions(self):
        """
        Get the biota reactions that are related to this network compound

        :return: The list of biota reactions corresponding to the chebi of kegg id. Returns [] is no biota reaction is found
        :rtype: `List[bioa.compound.reaction]` or SQL `select` resutls
        """

        if self.chebi_id:
            comp = BiotaCompound.get_or_none(BiotaCompound.chebi_id == self.chebi_id)
        elif self.kegg_id:
            comp = BiotaCompound.get_or_none(BiotaCompound.kegg_id == self.kegg_id)
        if comp is not None:
            return comp.reactions
        else:
            return None

    # -- I --

    def is_intracellular(self) -> bool:
        """
        Test if the compound is intracellular

        :return: True if the compound is intracellular, False otherwise
        :rtype: `bool`
        """

        return self.compartment.is_intracellular()

    def is_biomass(self) -> bool:
        """
        Test if the compound is the biomass compound

        :return: True if the compound is the biomass compound, False otherwise
        :rtype: `bool`
        """

        return self.compartment.is_biomass()

    def is_sink(self) -> bool:
        """
        Test if the compound is a sink compound

        :return: True if the compound is a sink compound, False otherwise
        :rtype: `bool`
        """

        return self.compartment.is_sink()

    def is_steady(self) -> bool:
        """
        Test if the compound is at steady state (is intracellular)

        :return: True if the compound is steady, False otherwise
        :rtype: `bool`
        """

        return self.compartment.is_steady

    def is_cofactor(self) -> bool:
        """
        Test if the compound is a factor

        :return: True if the compound is a cofactor, False otherwise
        :rtype: `bool`
        """

        return BiotaCofactor.is_cofactor(self.chebi_id, name=self.name, use_name_pattern=True)

    def is_residue(self) -> bool:
        """
        Test if the compound is a residue

        :return: True if the compound is a residue, False otherwise
        :rtype: `bool`
        """

        return BiotaResidue.is_residue(name=self.name)

    def get_type(self) -> bool:
        """
        Get the type of the compound
        """

        if self.is_cofactor():
            return self.COFACTOR_TYPE
        elif self.is_residue():
            return self.RESIDUE_TYPE
        else:
            return self.DEFAULT_TYPE

    # -- S --

    # def _set_network(self, network: 'Network'):
    #     """ Set the network """
    #     if self._network is not None:
    #         if self._network is not network:
    #             raise BadRequestException("The compound is already in a network")
    #     self._network = network

    # -- T --

    def to_str(self) -> str:
        """
        Returns a string representation of the compound

        :return: The string
        :rtype: `str`
        """

        _str = "" + \
            "================= Compound ===================" + \
            "\n id: " + self.id + \
            "\n charge: " + str(self.charge) + \
            "\n mass: " + str(self.mass) + \
            "\n formula: " + self.formula + \
            "\n chebi_id: " + self.chebi_id + \
            "=============================================="

        return _str
