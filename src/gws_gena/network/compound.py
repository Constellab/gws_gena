# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
from typing import List

from gws_biota import Cofactor as BiotaCofactor
from gws_biota import Compound as BiotaCompound
from gws_core import BadRequestException, Utils


def slugify_id(_id):
    return Utils.slugify(_id, snakefy=True, to_lower=False)

# ####################################################################
#
# CompoundPosition class
#
# ####################################################################


class CompoundPosition:
    """ Compount position """
    x: float = None
    y: float = None
    z: float = None
    is_major: bool = False

    def copy(self) -> 'CompoundPosition':
        p = CompoundPosition()
        p.x = self.x
        p.y = self.y
        p.z = self.z
        p.is_major = self.is_major
        return p

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
    position: CompoundPosition = None

    FLATTENING_DELIMITER = "_"
    COMPARTMENT_DELIMITER = "_"
    COMPARTMENT_CYTOSOL = "c"
    COMPARTMENT_NUCLEUS = "n"
    COMPARTMENT_MITOCHONDRION = "m"
    COMPARTMENT_BIOMASS = "b"
    COMPARTMENT_EXTRACELL = "e"
    COMPARTMENT_SINK = "s"
    COMPARTMENT_PERIPLASM = "p"

    # Use BiGG nomenclature for compartments
    COMPARTMENTS = {
        "c": {"name": "cytosol", "is_steady": True},
        "n": {"name": "nucleus", "is_steady": True},
        "m": {"name": "mitochondrion", "is_steady": True},
        "b": {"name": "biomass", "is_steady": False},
        "e": {"name": "extracellular", "is_steady": False},
        "s": {"name": "sink", "is_steady": False},
        "r": {"name": "endoplasmic reticulum", "is_steady": True},
        "v": {"name": "vacuole", "is_steady": True},
        "x": {"name": "peroxisome/glyoxysome", "is_steady": True},
        "g": {"name": "golgi apparatus", "is_steady": True},
        "p": {"name": "periplasm", "is_steady": True},
        "l": {"name": "lysosome", "is_steady": True},
        "o": {"name": "other", "is_steady": True}
    }

    LEVEL_MAJOR = "major"
    LEVEL_MINOR = "minor"
    LEVEL_COFACTOR = "cofactor"

    LEVEL_NUMBER = {
        LEVEL_MAJOR: 1,
        LEVEL_MINOR: 2,
        LEVEL_COFACTOR: 3
    }

    COFACTOR_NAME_PATTERNS = ["residue"]
    COFACTORS = BiotaCofactor.get_factors_as_list()

    def __init__(self, id="", name="", compartment=None,
                 formula="",
                 charge="", mass="", monoisotopic_mass="", inchi="",
                 inchikey="", chebi_id="", alt_chebi_ids: List = None, kegg_id=""):

        if chebi_id is None:
            chebi_id = ""
        if inchikey is None:
            inchikey = ""
        if not isinstance(chebi_id, str):
            raise BadRequestException("The chebi_id must be a string")
        if not isinstance(inchikey, str):
            raise BadRequestException("The inchikey must be a string")

        if not compartment:
            compartment = Compound.COMPARTMENT_CYTOSOL

        if len(compartment) == 1:
            if compartment not in self.COMPARTMENTS:
                raise BadRequestException(f"Invalid compartment '{compartment}'")
            compartment_suffix = compartment
        else:
            compartment_suffix = compartment.split(Compound.COMPARTMENT_DELIMITER)[-1]
            if compartment_suffix not in self.COMPARTMENTS:
                raise BadRequestException(f"Invalid compartment '{compartment}'")

        self.compartment = compartment

        if id:
            self.id = slugify_id(id)
            is_compartment_found = False
            for c in self.COMPARTMENTS:
                if self.id.endswith(Compound.COMPARTMENT_DELIMITER + c):
                    is_compartment_found = True
            if not is_compartment_found:
                raise BadRequestException(f"Invalid compound id '{self.id}'. No compartment suffix found.")
            # if not is_compartment_found:
            #    self.id = slugify_id(self.id + Compound.COMPARTMENT_DELIMITER + compartment_suffix)

            if not self.id.endswith(Compound.COMPARTMENT_DELIMITER + compartment_suffix):
                raise BadRequestException(
                    f"Invalid compound id '{self.id}'. The id suffix must be {compartment_suffix}.")
        else:
            # try to use inchikey or chebi compound name if possible
            is_found = False
            if not name:
                if inchikey:
                    try:
                        c = BiotaCompound.get(BiotaCompound.inchikey == inchikey)
                        name = c.get_name()
                        is_found = True
                    except Exception as _:
                        is_found = False

                if not is_found and chebi_id:
                    try:
                        c = BiotaCompound.get(BiotaCompound.chebi_id == chebi_id)
                        name = c.get_name()
                    except Exception as _:
                        name = chebi_id
                else:
                    raise BadRequestException("Please provide at least a valid compound id, name or chebi_id")

            self.id = slugify_id(name + Compound.COMPARTMENT_DELIMITER + compartment_suffix)

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
        self.position = CompoundPosition()

    # -- A --

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
        c.position = self.position.copy()
        return c

    @classmethod
    def create_sink_compound(cls, related_compound: 'Compound') -> 'Compound':
        """ Create a sink compound """
        if related_compound.compartment.endswith(Compound.COMPARTMENT_DELIMITER + Compound.COMPARTMENT_SINK):
            raise BadRequestException("Cannot add a sink reaction to another sink reaction")

        return Compound(
            id=related_compound.id + "_s",
            name=related_compound.name,
            compartment=Compound.COMPARTMENT_SINK,
            chebi_id=related_compound.chebi_id,
            inchikey=related_compound.inchikey,
        )

    # -- F --

    @classmethod
    def flatten_id(cls, id, ctx_name, is_compartment=False) -> str:
        """
        Flattens a compound or compartment id

        :param id: The id
        :type id: `str`
        :param ctx_name: The name of the (metabolic, biological, network) context
        :type ctx_name: `str`
        :param is_compartment: True if it is a compartment id, Otherwise it is a compound id
        :type is_compartment: `bool`
        :return: The flattened id
        :rtype: `str`
        """

        flat_delim = Compound.FLATTENING_DELIMITER
        skip_list = [cls.COMPARTMENT_EXTRACELL]
        for compart in skip_list:
            if id.endswith(Compound.COMPARTMENT_DELIMITER + compart) or (is_compartment and id == compart):
                return id
        return slugify_id(ctx_name + flat_delim + id.replace(flat_delim, Compound.COMPARTMENT_DELIMITER))

    @classmethod
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

        if not biota_compound:
            if inchikey:
                try:
                    biota_compound = BiotaCompound.get(BiotaCompound.inchikey == inchikey)
                except Exception as _:
                    pass

            if not biota_compound and chebi_id:
                if isinstance(chebi_id, (float, int)):
                    chebi_id = f"CHEBI:{chebi_id}"
                # if re.match(r"CHEBI\:\d+$", chebi_id):  # not in chebi_id:
                #     chebi_id = chebi_id
                try:
                    biota_compound = BiotaCompound.get(BiotaCompound.chebi_id == chebi_id)
                except Exception as _:
                    pass

            if not biota_compound and kegg_id:
                try:
                    biota_compound = BiotaCompound.get(BiotaCompound.kegg_id == kegg_id)
                except Exception as _:
                    pass

        if not biota_compound:
            raise BadRequestException(
                f"Cannot find compound (inchikey={inchikey}, chebi_id={chebi_id}, kegg_id={kegg_id})")

        if not compartment:
            compartment = Compound.COMPARTMENT_CYTOSOL
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

        # if biota_compound.position is not None:
        #     c.position.x = biota_compound.position.x
        #     c.position.y = biota_compound.position.y
        #     c.position.z = biota_compound.position.z
        #     c.position.is_major = biota_compound.position.is_major

        return c

    # -- G --

    def get_level(self, is_in_biomass_reaction=False) -> int:
        if self.is_major:
            level_str = self.LEVEL_MAJOR
        elif self.is_cofactor:
            level_str = self.LEVEL_COFACTOR
        else:
            level_str = self.LEVEL_MINOR

        # override if is in biomass_reaction
        if is_in_biomass_reaction:
            level_str = self.LEVEL_MAJOR

        return self.LEVEL_NUMBER[level_str]

    def get_related_biota_compound(self):
        """
        Get the biota compound that is related to this network compound

        :return: The biota compound corresponding to the chebi of kegg id. Returns `None` is no biota coumpund is found
        :rtype: `bioa.compound.Compound`, `None`
        """

        try:
            if self.chebi_id:
                return BiotaCompound.get(BiotaCompound.chebi_id == self.chebi_id)
            elif self.kegg_id:
                return BiotaCompound.get(BiotaCompound.kegg_id == self.kegg_id)
        except Exception as _:
            return None

    def get_related_biota_reactions(self):
        """
        Get the biota reactions that are related to this network compound

        :return: The list of biota reactions corresponding to the chebi of kegg id. Returns [] is no biota reaction is found
        :rtype: `List[bioa.compound.reaction]` or SQL `select` resutls
        """

        try:
            if self.chebi_id:
                comp = BiotaCompound.get(BiotaCompound.chebi_id == self.chebi_id)
            elif self.kegg_id:
                comp = BiotaCompound.get(BiotaCompound.kegg_id == self.kegg_id)

            return comp.reactions
        except Exception as _:
            return None

    # -- I --

    @property
    def is_intracellular(self) -> bool:
        """
        Test if the compound is intracellular

        :return: True if the compound is intracellular, False otherwise
        :rtype: `bool`
        """

        compartment_suffix = self.compartment.split(Compound.COMPARTMENT_DELIMITER)[-1]
        return compartment_suffix != self.COMPARTMENT_EXTRACELL and \
            compartment_suffix != self.COMPARTMENT_BIOMASS and \
            compartment_suffix != self.COMPARTMENT_SINK

    @property
    def is_biomass(self) -> bool:
        """
        Test if the compound is the biomass compound

        :return: True if the compound is the biomass compound, False otherwise
        :rtype: `bool`
        """

        compartment_suffix = self.compartment.split(Compound.COMPARTMENT_DELIMITER)[-1]
        return compartment_suffix == Compound.COMPARTMENT_BIOMASS

    @property
    def is_sink(self) -> bool:
        """
        Test if the compound is a sink compound

        :return: True if the compound is a sink compound, False otherwise
        :rtype: `bool`
        """

        compartment_suffix = self.compartment.split(Compound.COMPARTMENT_DELIMITER)[-1]
        return compartment_suffix == Compound.COMPARTMENT_SINK

    @property
    def is_steady(self) -> bool:
        """
        Test if the compound is at steady state (is intracellular)

        :return: True if the compound is steady, False otherwise
        :rtype: `bool`
        """

        compartment_suffix = self.compartment.split(Compound.COMPARTMENT_DELIMITER)[-1]
        return self.COMPARTMENTS[compartment_suffix]["is_steady"]

    @property
    def is_cofactor(self) -> bool:
        """
        Test if the compound is a factor

        :return: True if the compound is intracellular, False otherwise
        :rtype: `bool`
        """

        for pattern in self.COFACTOR_NAME_PATTERNS:
            if pattern in self.name:
                return not self.is_major
        return self.chebi_id in self.COFACTORS

    @property
    def is_major(self) -> bool:
        """
        Test if the compound is a major metabolite

        :return: True if the compound is intracellular, False otherwise
        :rtype: `bool`
        """

        if self.position.is_major:
            return self.position.is_major
        else:
            if self.is_biomass:
                return True
            return False

    @property
    def is_minor(self) -> bool:
        """
        Test if the compound is a minor metabolite
        """
        return (not self.is_cofactor) and (not self.is_major)

    # -- M --
