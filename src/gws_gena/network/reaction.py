# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
from typing import Dict, List

from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import Reaction as BiotaReaction
from gws_biota import ReactionLayoutDict as BiotaReactionLayoutDict
from gws_biota import Taxonomy as BiotaTaxo
from gws_core import BadRequestException

from ..deprecated.v032.retrocompatibilty import ReactionPosition
from .compound import Compound
from .helper.reaction_biota_helper import ReactionBiotaHelper
from .helper.slugify_helper import SlugifyHelper
from .typing.reaction_enzyme_typing import EnzymeDict, ReactionPathwayDict

FLATTENING_DELIMITER = ":"

# ####################################################################
#
# Exception classes
#
# ####################################################################


class ReactionNotFoundException(BadRequestException):
    """ ReactionNotFoundException """


class InvalidReactionIdException(BadRequestException):
    """ InvalidReactionIdException """


class SubstrateDuplicateException(BadRequestException):
    """ SubstrateDuplicateException """


class ProductDuplicateException(BadRequestException):
    """ ProductDuplicateException """


# ####################################################################
#
# Reaction class
#
# ####################################################################


class Reaction:
    """
    Class that represents a reaction of a network.

    Networks' reactions are proxy of biota reaction (i.e. Rhea compounds).
    They a used to build reconstructed digital twins.

    :property id: The id of the reaction
    :type id: `str`
    :property name: The name of the reaction
    :type name: `str`
    :property direction: The direction of the reaction. Bidirectional (B), Left direction (L), Righ direction (R)
    :type direction: `str`
    :property lower_bound: The lower bound of the reaction flux (metabolic flux)
    :type lower_bound: `float`
    :property upper_bound: The upper bound of the reaction flux (metabolic flux)
    :type upper_bound: `float`
    :property rhea_id: The corresponding Rhea if of the reaction
    :type rhea_id: `str`
    :property enzyme: The details on the enzyme that regulates the reaction
    :type enzyme: `dict`
    """

    LOWER_BOUND = -1000.0
    UPPER_BOUND = 1000.0

    id: str = ""
    name: str = ""
    direction: str = "B"
    lower_bound: float = LOWER_BOUND
    upper_bound: float = UPPER_BOUND
    rhea_id: str = ""
    enzyme: EnzymeDict = None

    layout: BiotaReactionLayoutDict = None
    # position: ReactionPosition = None  # will be depreacated soon

    _is_biomass_reaction = None
    _tax_ids = []
    _estimate: dict = None
    _substrates: dict = None
    _products: dict = None

    _FLATTENING_DELIMITER = FLATTENING_DELIMITER

    def __init__(self, id: str = "", name: str = "",
                 direction: str = "B", lower_bound: float = LOWER_BOUND, upper_bound: float = UPPER_BOUND,
                 enzyme: EnzymeDict = None, rhea_id=""):

        if id:
            self.id = SlugifyHelper.slugify_id(id)
        else:
            self.id = SlugifyHelper.slugify_id(name)

        self.name = name
        if enzyme is None:
            enzyme = {}
        self.enzyme = enzyme

        if not self.id:
            if self.enzyme:
                self.id = self.enzyme.get("ec_number", "")
                self.name = self.id

        if not self.id:
            raise InvalidReactionIdException("At least a valid reaction id or name is required")

        if direction in ["B", "L", "R"]:
            self.direction = direction

        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self._estimate = {}
        self._substrates = {}
        self._products = {}

        self.rhea_id = rhea_id
        self.layout = {}

    # -- A --

    def add_substrate(self, comp: Compound, stoich: float, update_if_exists=False):
        """
        Adds a substrate to the reaction

        :param comp: The compound to add as substrate
        :type comp: `gena.compound.Compound`
        :param stoich: The stoichiometry of the compound in the reaction
        :type stoich: `int`
        """

        if comp.id in self._substrates:
            if update_if_exists:
                self._substrates[comp.id]["stoichiometry"] += abs(float(stoich))
                return
            else:
                raise SubstrateDuplicateException("gena.reaction.Reaction", "add_substrate",
                                                  f"Substrate duplicate (id= {comp.id})")

        if comp.id in self._products:
            if update_if_exists:
                self._products[comp.id]["stoichiometry"] -= abs(float(stoich))
                if self._products[comp.id]["stoichiometry"] == 0.0:
                    self.remove_product(comp)
                return
            else:
                raise SubstrateDuplicateException(
                    "gena.reaction.Reaction", "add_substrate",
                    f"Cannot add the substrate. A product with the id already exists (id= {comp.id})")

        self._substrates[comp.id] = {
            "compound": comp,
            "stoichiometry": abs(float(stoich))
        }

    def add_product(self, comp: Compound, stoich: float, update_if_exists=False):
        """
        Adds a product to the reaction

        :param comp: The compound to add as product
        :type comp: `gena.compound.Compound`
        :param stoich: The stoichiometry of the compound in the reaction
        :type stoich: `int`
        """

        if comp.id in self._products:
            if update_if_exists:
                self._products[comp.id]["stoichiometry"] += abs(float(stoich))
                return
            else:
                raise ProductDuplicateException("gena.reaction.Reaction", "add_product",
                                                f"Product duplicate (id= {comp.id})")

        if comp.id in self._substrates:
            if update_if_exists:
                self._substrates[comp.id]["stoichiometry"] -= abs(float(stoich))
                if self._substrates[comp.id]["stoichiometry"] == 0.0:
                    self.remove_substrate(comp)
                return
            else:
                raise ProductDuplicateException(
                    "gena.reaction.Reaction", "add_substrate",
                    f"Cannot add the product. A susbtrate with the id already exists (id= {comp.id})")

        self._products[comp.id] = {
            "compound": comp,
            "stoichiometry": abs(float(stoich)),
        }

        if comp.is_biomass():
            self._is_biomass_reaction = True

    # -- C --

    def copy(self) -> 'Reaction':
        if self.layout is None:
            # check attribute for retro-compatiblity
            # TODO: remove on next major
            self.layout = {}

        rxn = Reaction(id=self.id, name=self.name)
        rxn.direction = self.direction
        rxn.lower_bound = self.lower_bound
        rxn.upper_bound = self.upper_bound
        rxn.rhea_id = self.rhea_id
        rxn.enzyme = self.enzyme
        rxn.layout = self.layout.copy()
        rxn._tax_ids = copy.deepcopy(self._tax_ids)
        rxn._estimate = copy.deepcopy(self._estimate)
        rxn._substrates = copy.deepcopy(self._substrates)
        rxn._products = copy.deepcopy(self._products)
        return rxn

    def compute_mass_and_charge_balance(self) -> dict:
        charge = 0.0
        mass = 0.0
        for sub in self.substrates.values():
            comp: Compound = sub["compound"]
            stoich = sub["stoichiometry"]
            if isinstance(comp.charge, float) and isinstance(charge, float):
                charge += stoich * comp.charge
            else:
                charge = None
            if isinstance(comp.mass, float) and isinstance(mass, float):
                mass += stoich * comp.mass
            else:
                mass = None

        for prod in self.products.values():
            comp: Compound = prod["compound"]
            stoich = prod["stoichiometry"]
            if isinstance(comp.charge, float) and isinstance(charge, float):
                charge -= stoich * comp.charge
            else:
                charge = None
            if isinstance(comp.mass, float) and isinstance(mass, float):
                mass -= stoich * comp.mass
            else:
                mass = None

        return {
            "mass": mass,
            "charge": charge
        }

    @classmethod
    def create_sink_reaction(self, related_compound: Compound = None, lower_bound: float = LOWER_BOUND,
                             upper_bound: float = UPPER_BOUND) -> 'Reaction':
        if not isinstance(related_compound, Compound):
            raise BadRequestException("A compound is required")
        name = related_compound.id + "_sink"
        rxn = Reaction(
            name=name,
            direction="B",
            lower_bound=lower_bound,
            upper_bound=upper_bound
        )
        sink_comp = Compound.create_sink_compound(related_compound=related_compound)
        rxn.add_substrate(related_compound, stoich=-1.0)
        rxn.add_product(sink_comp, stoich=1.0)
        return rxn

    # -- E --

    @property
    def estimate(self) -> dict:
        return self._estimate

    # -- F --

    @classmethod
    def flatten_id(cls, rxn_id: str, net_name: str) -> str:
        """
        Flattens a reaction id

        :param id: The id
        :type id: `str`
        :param net_name: The name of the network
        :type net_name: `str`
        :return: The flattened id
        :rtype: `str`
        """

        delim = cls._FLATTENING_DELIMITER
        return SlugifyHelper.slugify_id(net_name + delim + rxn_id)

    @classmethod
    def from_biota(
            cls, biota_reaction=None, rhea_id=None, ec_number=None, tax_id=None, tax_search_method='bottom_up') -> List['Reaction']:
        """
        Create a biota reaction from a Rhea id or an EC number.

        :param biota_reaction: The biota reaction to use. If not provided, the rhea_id or ec_number are used to fetch the corresponding reaction from the biota db.
        :type biota_reaction: `biota.compound.Compound`
        :param rhea_id: The Rhea id of the reaction. If given, the other parameters are not considered
        :rtype rhea_id: `str`
        :param ec_number: The EC number of the enzyme related to the reaction. If given, all the Rhea reactions associated with this enzyme are retrieved for the biota DB
        :rtype ec_number: `str`
        :param tax_id: The taxonomy ID of the target organism. If given, the enzymes are fetched in the corresponding taxonomy. If the taxonomy ID is not valid, no reaction is built.
        :rtype tax_id: `str`
        :param tax_search_method: The taxonomy search method (Defaults to `bottom_up`).
            * `none`: the algorithm will only search at the given taxonomy level
            * `bottom_up`: the algorithm will to traverse the taxonomy tree to search in the higher taxonomy levels until a reaction is found
        :rtype tax_search_method: `none` or `bottom_up`
        :rtype: `gena.reaction.Reaction`
        """

        rxns = []

        if biota_reaction:
            rhea_rxn = biota_reaction
            _added_rxns = []
            for e in rhea_rxn.enzymes:
                if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                    continue
                _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                rxns.append(ReactionBiotaHelper.create_reaction_from_biota(rhea_rxn, e))
            return rxns
        elif rhea_id:
            tax = None
            query = BiotaReaction.select().where(BiotaReaction.rhea_id == rhea_id)
            if len(query) == 0:
                raise BadRequestException(f"No reaction found with rhea_id {rhea_id}")
            _added_rxns = []
            for rhea_rxn in query:
                for e in rhea_rxn.enzymes:
                    if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                        continue
                    _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                    rxns.append(ReactionBiotaHelper.create_reaction_from_biota(rhea_rxn, e))
            return rxns
        elif ec_number:
            tax = None
            e = None
            if tax_id:
                tax = BiotaTaxo.get_or_none(BiotaTaxo.tax_id == tax_id)
                if tax is None:
                    raise BadRequestException(f"No taxonomy found with tax_id {tax_id}")

                query = BiotaEnzyme.select_and_follow_if_deprecated(
                    ec_number=ec_number, tax_id=tax_id, fields=['id'])

                if len(query) == 0:
                    if tax_search_method == 'bottom_up':
                        found_query = []
                        query = BiotaEnzyme.select_and_follow_if_deprecated(ec_number=ec_number)
                        tab = {}
                        for e in query:
                            if not e.ec_number in tab:
                                tab[e.ec_number] = []
                            tab[e.ec_number].append(e)
                        for t in tax.ancestors:
                            is_found = False
                            for _, ec in enumerate(tab):
                                e_group = tab[ec]
                                for e in e_group:
                                    if t.rank == "no rank":
                                        continue
                                    if getattr(e, "tax_"+t.rank) == t.tax_id:
                                        found_query.append(e)
                                        is_found = True
                                        break  # -> stop at this taxonomy rank
                                if is_found:
                                    del tab[ec]
                                    break
                        # add remaining enzyme
                        for e_group in tab.values():
                            for e in e_group:
                                found_query.append(e)
                                break
                        if found_query:
                            query = found_query

                if len(query) == 0:
                    raise BadRequestException(f"No enzyme found with ec_number {ec_number} and tax_id {tax_id}")
                _added_rxns = []
                for e in query:
                    for rhea_rxn in e.reactions:
                        if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                            continue
                        _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                        rxns.append(ReactionBiotaHelper.create_reaction_from_biota(rhea_rxn, e))
                if not rxns:
                    raise BadRequestException(f"No reactions found with ec_number {ec_number}.")
            else:
                query = BiotaEnzyme.select_and_follow_if_deprecated(
                    ec_number=ec_number, fields=['id'])
                if len(query) == 0:
                    raise BadRequestException(f"No enzyme found with ec_number {ec_number}")
                _added_rxns = []
                for e in query:
                    for rhea_rxn in e.reactions:
                        if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                            continue
                        _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                        rxns.append(ReactionBiotaHelper.create_reaction_from_biota(rhea_rxn, e))
                if not rxns:
                    raise BadRequestException(f"No reactions found with ec_number {ec_number}")
        else:
            raise BadRequestException("Invalid arguments")

        return rxns

    # -- G --

    def get_pathways(self) -> ReactionPathwayDict:
        if self.enzyme.get("pathways"):
            return self.enzyme.get("pathways")

        return ReactionPathwayDict()

    def get_pathways_as_flat_dict(self) -> Dict:
        pw_dict = {}
        pw = self.get_pathways()
        if pw:
            bkms = ['brenda', 'kegg', 'metacyc']
            for db_name in bkms:
                if pw.get(db_name):
                    pw_dict[db_name] = pw[db_name]["name"] + \
                        " (" + (pw[db_name]["id"] if pw[db_name]["id"] else "--") + ")"
            return pw_dict
        else:
            return {"kegg": "", "brenda": "", "metacyc": ""}

    # -- I --

    def is_biomass_reaction(self):
        # retro-rcomaptiblity check
        if self._is_biomass_reaction is None:
            self._is_biomass_reaction = False
            for comp_id in self.products:
                comp = self.products[comp_id]["compound"]
                if comp.is_biomass():
                    self._is_biomass_reaction = True
                    break

        return self._is_biomass_reaction

    def has_products(self):
        return bool(self._products)

    def has_substrates(self):
        return bool(self._substrates)

    def is_empty(self):
        return not self.has_substrates() and not self.has_products()

    # -- P --

    @property
    def products(self) -> str:
        """
        Returns the products of the reaction

        :return: The list of products as {key,value} dictionnary
        :rtype: `dict`
        """

        return self._products

    # -- R --

    def remove_substrate(self, comp: Compound):
        """
        Removes a substrate to the reaction

        :param comp: The compound to remove
        :type comp: `gena.compound.Compound`
        """

        if not comp.id in self._substrates:
            raise BadRequestException(f"Substrate (id= {comp.id}) does not exist")

        # remove the compound from the reaction
        del self._substrates[comp.id]

    def remove_product(self, comp: Compound):
        """
        Remove a product to the reaction

        :param comp: The compound to remove
        :type comp: `gena.compound.Compound`
        """

        if not comp.id in self._products:
            raise BadRequestException(f"Product (id= {comp.id}) does not exist")

        # remove the compound from the reaction
        del self._products[comp.id]

        if comp.is_biomass():
            self._is_biomass_reaction = True

    def get_related_biota_reaction(self):
        """
        Get the biota reaction that is related to this reaction

        :return: The biota compound corresponding to the rhea id. Returns `None` is no biota reaction is found
        :rtype: `bioa.reaction.Reaction`, `None`
        """

        return BiotaReaction.get_or_none(BiotaReaction.rhea_id == self.rhea_id)

    # -- S --

    def set_estimate(self, estimate: dict):
        if not "value" in estimate:
            BadRequestException("No value in estimate data")

        if not "lower_bound" in estimate:
            BadRequestException("No lower_bound in estimate data")

        if not "upper_bound" in estimate:
            BadRequestException("No upper_bound in estimate data")

        self._estimate = estimate

    def set_enzyme(self, enzyme: EnzymeDict):
        self.enzyme = enzyme

    @property
    def substrates(self) -> dict:
        """
        Returns the substrates of the reaction

        :return: The list of substrates as {key,value} dictionnary
        :rtype: `dict`
        """

        return self._substrates

    # -- T --

    def to_str(self, show_ids=False, show_mass=False, show_charge=False) -> str:
        """
        Returns a string representation of the reaction

        :return: The string
        :rtype: `str`
        """

        _left = []
        _right = []
        _dir = {"L": " <==(E)== ", "R": " ==(E)==> ", "B": " <==(E)==> "}

        for k in self._substrates:
            sub = self._substrates[k]
            comp = sub["compound"]
            stoich = sub["stoichiometry"]
            if show_ids:
                _id = comp.chebi_id if comp.chebi_id else comp.id
                _left.append(f"({stoich}) {_id}")
            else:
                _left.append(f"({stoich}) {comp.id}")

        for k in self._products:
            prod = self._products[k]
            comp = prod["compound"]
            stoich = prod["stoichiometry"]
            if show_ids:
                _id = comp.chebi_id if comp.chebi_id else comp.id
                _right.append(f"({stoich}) {_id}")
            else:
                _right.append(f"({stoich}) {comp.id}")

        if not _left:
            _left = ["*"]

        if not _right:
            _right = ["*"]

        _str = " + ".join(_left) + _dir[self.direction].replace("E",
                                                                self.enzyme.get("ec_number", "")) + " + ".join(_right)
        #_str = _str + " " + str(self.enzyme)
        return _str
