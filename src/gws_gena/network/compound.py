# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
from typing import List

from gws_biota import Cofactor as BiotaCofactor
from gws_biota import Compound as BiotaCompound
from gws_biota import CompoundClusterDict as BiotaCompoundClusterDict
from gws_biota import CompoundLayout as BiotaCompoundLayout
from gws_biota import CompoundLayoutDict as BiotaCompoundLayoutDict
from gws_core import BadRequestException, Utils

from ..deprecated.v032.retrocompatibilty import CompoundPosition
from .compartment import Compartment
from .helper.layout_helper import LayoutHelper
from .helper.slugify_helper import SlugifyHelper

# ####################################################################
#
# Exception classes
#
# ####################################################################


class CompoundNotFoundException(BadRequestException):
    """ CompoundNotFoundException """


class InvalidCompoundIdException(BadRequestException):
    """ InvalidCompoundIdException """


# ####################################################################
#
# Compound class
#
# ####################################################################


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

    id = ""
    name = ""
    charge = None
    mass = None
    monoisotopic_mass = None
    formula = ""
    inchi = ""
    compartment = ""
    chebi_id = ""
    alt_chebi_ids: List = None
    kegg_id = ""
    inchikey = ""
    layout: BiotaCompoundLayoutDict = None
    # position: CompoundPosition = None

    FLATTENING_DELIMITER = "_"

    LEVEL_MAJOR = 1
    LEVEL_MINOR = 2
    LEVEL_COFACTOR = 3

    def __init__(self, id="", name="", compartment=None, formula="", charge="", mass="", monoisotopic_mass="", inchi="",
                 inchikey="", chebi_id="", alt_chebi_ids: List = None, kegg_id="", layout: BiotaCompoundLayoutDict = None):

        if chebi_id is None:
            chebi_id = ""
        if inchikey is None:
            inchikey = ""
        if not isinstance(chebi_id, str):
            raise BadRequestException("The chebi_id must be a string")
        if not isinstance(inchikey, str):
            raise BadRequestException("The inchikey must be a string")

        if not compartment:
            compartment = Compartment.CYTOSOL

        compartment_suffix = Compartment.check_and_retrieve_suffix(compartment)
        self.compartment = compartment

        if id:
            self.id = SlugifyHelper.slugify_id(id)
            id_compartment_suffix = Compartment.retrieve_suffix_from_compound_id(self.id)
            if id_compartment_suffix is None:
                raise InvalidCompoundIdException(f"Invalid compound id '{self.id}'. No compartment suffix found.")

            # ensure that the compartment suffix is compatible with the compound id
            if id_compartment_suffix != compartment_suffix:
                raise InvalidCompoundIdException(
                    f"Invalid compound id '{self.id}'. The id suffix must be {compartment_suffix}.")
        else:
            if not name:

                # if not is_found and chebi_id:
                if chebi_id:
                    c = BiotaCompound.get_or_none(BiotaCompound.chebi_id == chebi_id)
                    if c is not None:
                        name = c.get_name()
                    else:
                        name = chebi_id
                else:
                    # raise CompoundNotFoundException("The chebi_id and inchikey are not valid")
                    raise CompoundNotFoundException("The chebi_id is not valid")

            self.id = SlugifyHelper.slugify_id(name + Compartment.DELIMITER + compartment_suffix)

        if not name:
            name = self.id

        self.name = name
        self.charge = charge
        self.mass = mass
        self.monoisotopic_mass = monoisotopic_mass
        self.formula = formula
        self.inchi = inchi
        self.inchikey = inchikey
        self.chebi_id = chebi_id
        self.kegg_id = kegg_id
        self.alt_chebi_ids = (alt_chebi_ids if alt_chebi_ids else [])

        if layout is not None:
            self.layout = layout
        else:
            # refresh layout
            self.layout: BiotaCompoundLayoutDict = BiotaCompoundLayout.get_layout_by_chebi_id(
                synonym_chebi_ids=chebi_id,
                compartment=self.compartment)

        if self.is_biomass():
            self.append_biomass_layout(is_biomass=True)

    # -- A --

    def append_biomass_layout(self, is_biomass=False):
        """ Append biomass layout """
        if self.layout is None:
            # check attribute for retro-compatiblity
            # TODO: remove on next major
            self.layout = {}

        if "clusters" not in self.layout:
            self.layout["clusters"] = {}

        self.layout["clusters"].update(
            LayoutHelper.create_biomass_layout(is_biomass=is_biomass)["clusters"]
        )

    # -- C --

    def copy(self) -> 'Compound':
        """ Create a copy of the compound """
        c = Compound(id=self.id, name=self.name, compartment=self.compartment)
        c.charge = self.charge
        c.mass = self.mass
        c.monoisotopic_mass = self.monoisotopic_mass
        c.formula = self.formula
        c.inchi = self.inchi
        c.chebi_id = self.chebi_id
        c.alt_chebi_ids = copy.deepcopy(self.alt_chebi_ids)
        c.kegg_id = self.kegg_id
        c.inchikey = self.inchikey
        return c

    @ classmethod
    def create_sink_compound(cls, related_compound: 'Compound') -> 'Compound':
        """ Create a sink compound """
        if related_compound.compartment.endswith(Compartment.DELIMITER + Compartment.SINK):
            raise BadRequestException("Cannot add a sink reaction to another sink reaction")

        return Compound(
            id=related_compound.id + "_s",
            name=related_compound.name,
            compartment=Compartment.SINK,
            chebi_id=related_compound.chebi_id,
            inchikey=related_compound.inchikey,
        )

    # -- F --

    @ classmethod
    def flatten_compound_id(cls, comp_id, net_name) -> str:
        """
        Flattens a compound id

        :param comp_id: The id
        :type comp_id: `str`
        :param net_name: The name of the (metabolic, biological, network) context
        :type net_name: `str`
        :return: The flattened id
        :rtype: `str`
        """

        flat_delim = Compound.FLATTENING_DELIMITER
        skip_list = [Compartment.EXTRACELLULAR_SPACE]
        for compart in skip_list:
            if comp_id.endswith(Compartment.DELIMITER + compart):
                return comp_id
        return SlugifyHelper.slugify_id(net_name + flat_delim + comp_id)

    @ classmethod
    def flatten_compartment_id(cls, comp_id, net_name) -> str:
        """
        Flattens a compartment id

        :param comp_id: The id
        :type comp_id: `str`
        :param net_name: The name of the (metabolic, biological, network) context
        :type net_name: `str`
        :return: The flattened id
        :rtype: `str`
        """

        flat_delim = Compound.FLATTENING_DELIMITER
        skip_list = [Compartment.EXTRACELLULAR_SPACE]
        for compart in skip_list:
            if comp_id.endswith(Compartment.DELIMITER + compart) or comp_id == compart:
                return comp_id
        return SlugifyHelper.slugify_id(net_name + flat_delim + comp_id)

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
    def from_biota(
            cls, id=None, name="", biota_compound=None, chebi_id="", kegg_id="", inchikey="", compartment="") -> 'Compound':
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
            # raise CompoundNotFoundException(
            #     f"Cannot find compound (chebi_id={chebi_id}, inchikey={inchikey}, kegg_id={kegg_id})")

        if not compartment:
            compartment = Compartment.CYTOSOL
        if not name:
            name = biota_compound.name

        c = Compound(
            id=id,
            name=name,
            compartment=compartment,
            chebi_id=biota_compound.chebi_id,
            kegg_id=biota_compound.kegg_id,
            inchikey=biota_compound.inchikey,
            charge=biota_compound.charge,
            formula=biota_compound.formula,
            mass=biota_compound.mass,
            monoisotopic_mass=biota_compound.monoisotopic_mass,
        )

        return c

    # -- G --

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

        return Compartment.is_intracellular(self.compartment)

    def is_biomass(self) -> bool:
        """
        Test if the compound is the biomass compound

        :return: True if the compound is the biomass compound, False otherwise
        :rtype: `bool`
        """

        return Compartment.is_biomass(self.compartment)

    def is_sink(self) -> bool:
        """
        Test if the compound is a sink compound

        :return: True if the compound is a sink compound, False otherwise
        :rtype: `bool`
        """

        return Compartment.is_sink(self.compartment)

    def is_steady(self) -> bool:
        """
        Test if the compound is at steady state (is intracellular)

        :return: True if the compound is steady, False otherwise
        :rtype: `bool`
        """

        return Compartment.is_steady(self.compartment)

    def is_cofactor(self) -> bool:
        """
        Test if the compound is a factor

        :return: True if the compound is intracellular, False otherwise
        :rtype: `bool`
        """

        return BiotaCofactor.is_cofactor(self.chebi_id, name=self.name, use_name_pattern=True)
