# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
from typing import Dict, List, Union

from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import Reaction as BiotaReaction
from gws_biota import ReactionLayoutDict as BiotaReactionLayoutDict
from gws_core import BadRequestException

from ..compound.compound import Compound
from ..exceptions.compound_exceptions import (ProductDuplicateException,
                                              SubstrateDuplicateException)
from ..exceptions.reaction_exceptions import InvalidReactionException
from ..helper.numeric_helper import NumericHelper
from ..reaction.helper.reaction_biota_helper import ReactionBiotaHelper
from ..reaction.reaction_compound import Product, Substrate
from ..typing.enzyme_typing import EnzymeDict
from ..typing.pathway_typing import ReactionPathwayDict
from ..typing.reaction_typing import ReactionDict
from .helper.enzyme_search_up_helper import EnzymeSearchUpHelper


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
    :property enzymes: The details on the enzymes that regulates the reaction
    :type enzymes: `list[dict]`
    """

    LOWER_BOUND = -1000.0
    UPPER_BOUND = 1000.0

    id: str = ""
    name: str = ""
    direction: str = "B"
    lower_bound: float = LOWER_BOUND
    upper_bound: float = UPPER_BOUND
    rhea_id: str = ""
    enzymes: List[EnzymeDict] = None
    products: Dict[str, Product] = None
    substrates: Dict[str, Substrate] = None
    data: dict = None
    layout: BiotaReactionLayoutDict = None

    def __init__(self, dict_: ReactionDict = None):
        if dict_ is None:
            dict_ = {}
        for key, val in dict_.items():
            setattr(self, key, val)

        if not self.id:
            if not self.name:
                if self.rhea_id:
                    self.name = self.rhea_id
                else:
                    raise InvalidReactionException("The reaction name or rhea_id is required")

            if self.rhea_id:
                self.id = self.rhea_id
            else:
                self.id = self.name

        if not self.name:
            self.name = self.id

        # enzymes
        if self.enzymes is None:
            self.enzymes = []

        if not self.id:
            raise InvalidReactionException("A valid reaction id or name is required")

        if self.direction not in ["B", "L", "R"]:
            self.direction = "B"

        if self.substrates is None:
            self.substrates = {}

        if self.products is None:
            self.products = {}

        if self.data is None:
            self.data = {}

        if self.layout is None:
            self.layout = {}

    # -- A --

    def add_data_slot(self, slot: str, data: dict):
        """ Set data """
        self.data[slot] = data

    def add_substrate(
            self, comp: Compound, stoich: float, network: Union['Network', 'NetworkData'] = None, update_if_exists=False):
        """
        Adds a substrate to the reaction

        :param comp: The compound to add as substrate
        :type comp: `gena.compound.Compound`
        :param stoich: The stoichiometry of the compound in the reaction
        :type stoich: `int`
        """

        from ..network import Network
        from ..network_data.network_data import NetworkData
        if not isinstance(comp, Compound):
            raise BadRequestException("The compound must be an instance of Compound")
        if not NumericHelper.isfloat(stoich):
            raise BadRequestException(f"The stoichiometry must be a float. Current value is {stoich}.")
        if (network is not None) and (not isinstance(network, (Network, NetworkData))):
            raise BadRequestException("The network must be an instance of Network or NetworkData")

        if comp.id in self.substrates:
            if update_if_exists:
                substrate = self.substrates[comp.id]
                substrate.stoich += abs(float(stoich))
                return
            else:
                raise SubstrateDuplicateException(
                    f"Substrate duplicate (rxn_id={self.rhea_id}, rxn_rhea={self.rhea_id}, comp_id= {comp.id})")

        if (network is not None) and (not network.compound_exists(comp)):
            network.add_compound(comp)
        self.substrates[comp.id] = Substrate(comp, stoich)

    def add_product(
            self, comp: Compound, stoich: float, network: Union['Network', 'NetworkData'] = None, update_if_exists=False):
        """
        Adds a product to the reaction

        :param comp: The compound to add as product
        :type comp: `gena.compound.Compound`
        :param stoich: The stoichiometry of the compound in the reaction
        :type stoich: `int`
        """

        from ..network import Network
        from ..network_data.network_data import NetworkData
        if not isinstance(comp, Compound):
            raise BadRequestException("The compound must be an instance of Compound")
        if not NumericHelper.isfloat(stoich):
            raise BadRequestException(f"The stoichiometry must be a float. Current value is {stoich}.")
        if (network is not None) and (not isinstance(network, (Network, NetworkData))):
            raise BadRequestException("The network must be an instance of Network")

        if comp.id in self.products:
            if update_if_exists:
                product = self.products[comp.id]
                product.stoich += abs(float(stoich))
                return
            else:
                raise ProductDuplicateException("gena.reaction.Reaction", "add_product",
                                                f"Product duplicate (id= {comp.id})")

        if (network is not None) and (not network.compound_exists(comp)):
            network.add_compound(comp)

        self.products[comp.id] = Product(comp, stoich)

    # -- C --

    def copy(self) -> 'Reaction':
        """ Deep copy """
        if self.layout is None:
            # check attribute for retro-compatiblity
            # TODO: remove on next major
            self.layout = {}

        rxn = Reaction(ReactionDict(id=self.id, name=self.name))
        rxn.direction = self.direction
        rxn.lower_bound = self.lower_bound
        rxn.upper_bound = self.upper_bound
        rxn.rhea_id = self.rhea_id
        rxn.enzymes = self.enzymes

        rxn.layout = self.layout.copy()
        rxn.data = copy.deepcopy(self.data)
        rxn.substrates = {k: v.copy() for k, v, in self.substrates.items()}
        rxn.products = {k: v.copy() for k, v in self.products.items()}
        return rxn

    def compute_mass_and_charge_balance(self) -> dict:
        """ Compute the mass and charge balance of a reaction """
        def _compute_blance(val, stoich, comp_val):
            if isinstance(val, float):
                if isinstance(comp_val, str) and len(comp_val) != 0:
                    val += stoich * float(comp_val)
                elif isinstance(comp_val, float):
                    val += stoich * comp_val
                else:
                    val = None
            else:
                val = None
            return val

        charge = 0.0
        mass = 0.0

        for substrate in self.substrates.values():
            comp = substrate.compound
            stoich = substrate.stoich
            charge = _compute_blance(charge, stoich, comp.charge)
            mass = _compute_blance(mass, stoich, comp.mass)

        for product in self.products.values():
            comp = product.compound
            stoich = product.stoich
            charge = _compute_blance(charge, -stoich, comp.charge)
            mass = _compute_blance(mass, -stoich, comp.mass)

        return {"mass": mass, "charge": charge}

    @ classmethod
    def create_sink_reaction(cls, related_compound: Compound, network: Union['Network', 'NetworkData'],
                             lower_bound: float = LOWER_BOUND, upper_bound: float = UPPER_BOUND) -> 'Reaction':
        if not isinstance(related_compound, Compound):
            raise BadRequestException("A compound is required")
        name = related_compound.id + "_sink"
        rxn = Reaction(
            ReactionDict(
                name=name,
                direction="B",
                lower_bound=lower_bound,
                upper_bound=upper_bound
            ))
        sink_comp = Compound.create_sink_compound(related_compound=related_compound)
        rxn.add_substrate(related_compound, -1.0, network)
        rxn.add_product(sink_comp, 1.0, network)
        return rxn

    # -- E --

    # -- F --

    @ classmethod
    def from_biota(cls, *, biota_reaction=None, rhea_id=None, ec_number=None, tax_id=None,
                   tax_search_method='bottom_up') -> List['Reaction']:
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

        rxn_biota_helper = ReactionBiotaHelper()

        if biota_reaction:
            return [rxn_biota_helper.create_reaction_from_biota(rhea_rxn=biota_reaction)]
        elif rhea_id:
            query = BiotaReaction.select().where(BiotaReaction.rhea_id == rhea_id)
            if len(query) == 0:
                raise BadRequestException(f"No reaction found with rhea_id {rhea_id}")
            else:
                biota_reaction = query[0]
                return [rxn_biota_helper.create_reaction_from_biota(rhea_rxn=biota_reaction)]
        elif ec_number:
            biota_reaction_dict = {}
            if tax_id:
                query = EnzymeSearchUpHelper.search(ec_number, tax_id, tax_search_method=tax_search_method)

                if len(query) == 0:
                    raise BadRequestException(f"No enzyme found with ec_number {ec_number} and tax_id {tax_id}")

                for biota_enzyme in query:
                    for rhea_rxn in biota_enzyme.reactions:
                        biota_reaction_dict[rhea_rxn.id] = rhea_rxn
            else:
                query = BiotaEnzyme.select_and_follow_if_deprecated(
                    ec_number=ec_number, fields=['id', 'ec_number'])
                if len(query) == 0:
                    raise BadRequestException(f"No enzyme found with ec_number {ec_number}")
                for biota_enzyme in query:
                    for rhea_rxn in biota_enzyme.reactions:
                        biota_reaction_dict[rhea_rxn.id] = rhea_rxn

            if len(biota_reaction_dict) == 0:
                raise BadRequestException(f"No biota reactions found with ec_number {ec_number}")

            rxns = []
            built_rxns = []
            for biota_reaction in biota_reaction_dict.values():
                built_rxns.append(biota_reaction.id)
                rxns.append(rxn_biota_helper.create_reaction_from_biota(rhea_rxn=biota_reaction))
            return rxns
        else:
            raise BadRequestException("Invalid parameters")

    # -- G --

    def get_pathways(self) -> ReactionPathwayDict:
        if len(self.enzymes) == 0:
            return ReactionPathwayDict({})
        else:
            if self.enzymes[0].get("pathways"):
                return self.enzymes[0].get("pathways")
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

    def get_data_slot(self, slot: str, default=None):
        """ Set data """
        return self.data.get(slot, default)

    # -- I --

    def is_biomass_reaction(self):
        """ Returns True, if it is the biomass reaction; False otherwise """
        tf = False
        for product in self.products.values():
            comp = product.compound
            if comp.is_biomass():
                tf = True
                break
        return tf

    def has_products(self):
        """ has products """
        return bool(self.products)

    def has_substrates(self):
        """ has substrates """
        return bool(self.substrates)

    def is_empty(self):
        """ is empty """
        return not self.has_substrates() and not self.has_products()

    # -- P --

    # -- R --

    def remove_substrate(self, comp: Compound):
        """
        Removes a substrate to the reaction

        :param comp: The compound to remove
        :type comp: `gena.compound.Compound`
        """

        if not comp.id in self.substrates:
            raise BadRequestException(f"Substrate (id= {comp.id}) does not exist")

        # remove the compound from the reaction
        del self.substrates[comp.id]

    def remove_product(self, comp: Compound):
        """
        Remove a product to the reaction

        :param comp: The compound to remove
        :type comp: `gena.compound.Compound`
        """

        if not comp.id in self.products:
            raise BadRequestException(f"Product (id= {comp.id}) does not exist")

        # remove the compound from the reaction
        del self.products[comp.id]

    def get_related_biota_reaction(self):
        """
        Get the biota reaction that is related to this reaction

        :return: The biota compound corresponding to the rhea id. Returns `None` is no biota reaction is found
        :rtype: `bioa.reaction.Reaction`, `None`
        """

        return BiotaReaction.get_or_none(BiotaReaction.rhea_id == self.rhea_id)

    # -- S --

    def set_data(self, data: dict):
        """ Set data """
        if not isinstance(data, dict):
            raise BadRequestException("The data must be a dictionary")
        self.data = data

    # -- T --

    def to_str(self, show_names=False) -> str:
        """
        Returns a string representation of the reaction

        :return: The string
        :rtype: `str`
        """

        left_ = []
        right_ = []
        dir_ = {"L": " <==(E)== ", "R": " ==(E)==> ", "B": " <==(E)==> "}

        for comp_id, substrate in self.substrates.items():
            comp = substrate.compound
            stoich = substrate.stoich
            if show_names:
                left_.append(f"({stoich}) {comp.name}")
            else:
                left_.append(f"({stoich}) {comp.id}")

        for comp_id, product in self.products.items():
            comp = product.compound
            stoich = product.stoich
            if show_names:
                right_.append(f"({stoich}) {comp.name}")
            else:
                right_.append(f"({stoich}) {comp.id}")

        if not left_:
            left_ = ["*"]

        if not right_:
            right_ = ["*"]

        ec_number = list(set([e.get("ec_number", "") for e in self.enzymes]))
        str_ = " + ".join(left_) + \
            dir_[self.direction].replace("E", ",".join(ec_number)) + " + ".join(right_)

        return str_
