# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
from typing import Dict, List, TypedDict, Union

from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import Reaction as BiotaReaction
from gws_biota import ReactionLayoutDict as BiotaReactionLayoutDict
from gws_biota import Taxonomy as BiotaTaxo
from gws_core import BadRequestException

from ..compound.compound import Compound
from ..exceptions.compound_exceptions import (ProductDuplicateException,
                                              SubstrateDuplicateException)
from ..exceptions.reaction_exceptions import InvalidReactionException
from ..helper.numeric_helper import NumericHelper
from ..helper.slugify_helper import SlugifyHelper
from ..reaction.helper.reaction_biota_helper import ReactionBiotaHelper
from ..reaction.reaction_compound import Product, Substrate
from ..typing.enzyme_typing import EnzymeDict
from ..typing.pathway_typing import ReactionPathwayDict
from ..typing.reaction_typing import ReactionDict


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
    products: Dict[str, Product] = None
    substrates: Dict[str, Substrate] = None
    data: dict = None
    layout: BiotaReactionLayoutDict = None

    def __init__(self, dict_: ReactionDict = None):
        if dict_ is None:
            dict_ = {}
        for key, val in dict_.items():
            setattr(self, key, val)

        if self.id:
            self.id = SlugifyHelper.slugify_id(self.id)
        else:
            self.id = SlugifyHelper.slugify_id(self.name)

        if self.enzyme is None:
            self.enzyme = {}

        if not self.id:
            if self.enzyme:
                self.id = self.enzyme.get("ec_number", "")
                self.name = self.id

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
                raise SubstrateDuplicateException("gena.reaction.Reaction", "add_substrate",
                                                  f"Substrate duplicate (id= {comp.id})")

        # is_also_product = comp.id in self.product_stoichs
        # if is_also_product:
        #     if update_if_exists:
        #         self.product_stoichs[comp.id] -= abs(float(stoich))
        #         if self.product_stoichs[comp.id] == 0.0:
        #             self.remove_product(comp)
        #         return
        #     else:
        #         raise SubstrateDuplicateException(
        #             "gena.reaction.Reaction", "add_substrate",
        #             f"Cannot add the substrate. A product with the id already exists (id= {comp.id})")

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
        rxn.enzyme = self.enzyme
        rxn.layout = self.layout.copy()
        rxn.data = copy.deepcopy(self.data)
        rxn.substrates = {k: v.copy() for k, v, in self.substrates.items()}
        rxn.products = {k: v.copy() for k, v in self.products.items()}
        return rxn

    def compute_mass_and_charge_balance(self) -> dict:
        """ Compute the mass and charge balance of a reaction """
        charge = 0.0
        mass = 0.0

        for substrate in self.substrates.values():
            comp = substrate.compound
            stoich = substrate.stoich
            if isinstance(charge, float) and isinstance(comp.charge, float):
                charge += stoich * comp.charge
            else:
                charge = None
            if isinstance(mass, float) and isinstance(comp.mass, float):
                mass += stoich * comp.mass
            else:
                mass = None

        for product in self.products.values():
            comp = product.compound
            stoich = product.stoich
            if isinstance(charge, float) and isinstance(comp.charge, float):
                charge -= stoich * comp.charge
            else:
                charge = None
            if isinstance(mass, float) and isinstance(comp.mass, float):
                mass -= stoich * comp.mass
            else:
                mass = None

        return {
            "mass": mass,
            "charge": charge
        }

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

    # @ classmethod
    # def flatten_id(cls, rxn_id: str, net_name: str) -> str:
    #     """
    #     Flattens a reaction id

    #     :param id: The id
    #     :type id: `str`
    #     :param net_name: The name of the network
    #     :type net_name: `str`
    #     :return: The flattened id
    #     :rtype: `str`
    #     """

    #     delim = cls._FLATTENING_DELIMITER
    #     return SlugifyHelper.slugify_id(net_name + delim + rxn_id)

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

        rxns = []
        rxn_biota_helper = ReactionBiotaHelper()

        if biota_reaction:
            rhea_rxn = biota_reaction
            _added_rxns = []
            for e in rhea_rxn.enzymes:
                if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                    continue
                _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                rxns.append(rxn_biota_helper.create_reaction_from_biota(rhea_rxn, e))
            return rxns
        elif rhea_id:
            tax = None
            query = BiotaReaction.select().where(BiotaReaction.rhea_id == rhea_id)
            if len(query) == 0:
                raise BadRequestException(f"No reaction found with rhea_id {rhea_id}")
            _added_rxns = []
            for rhea_rxn in query:
                if len(rhea_rxn.enzymes) == 0:
                    # TODO: To delete after
                    # temporary fix
                    # -----------------------------
                    _added_rxns.append(rhea_rxn.rhea_id)
                    rxns.append(rxn_biota_helper.create_reaction_from_biota(rhea_rxn, None))
                    # -----------------------------
                else:
                    for e in rhea_rxn.enzymes:
                        if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                            continue
                        _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                        rxns.append(rxn_biota_helper.create_reaction_from_biota(rhea_rxn, e))
            return rxns
        elif ec_number:
            tax = None
            e = None
            if tax_id:
                tax = BiotaTaxo.get_or_none(BiotaTaxo.tax_id == tax_id)
                if tax is None:
                    raise BadRequestException(f"No taxonomy found with tax_id {tax_id}")

                query = BiotaEnzyme.select_and_follow_if_deprecated(
                    ec_number=ec_number, tax_id=tax_id, fields=['id', 'ec_number'])

                if len(query) == 0:
                    if tax_search_method == 'bottom_up':
                        found_query = []
                        query = BiotaEnzyme.select_and_follow_if_deprecated(ec_number=ec_number)
                        tab = {}
                        for e in query:
                            if e.ec_number not in tab:
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
                        rxns.append(rxn_biota_helper.create_reaction_from_biota(rhea_rxn, e))
                if not rxns:
                    raise BadRequestException(f"No reactions found with ec_number {ec_number}.")
            else:
                query = BiotaEnzyme.select_and_follow_if_deprecated(
                    ec_number=ec_number, fields=['id', 'ec_number'])
                if len(query) == 0:
                    raise BadRequestException(f"No enzyme found with ec_number {ec_number}")
                _added_rxns = []
                for e in query:
                    for rhea_rxn in e.reactions:
                        if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                            continue
                        _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                        rxns.append(rxn_biota_helper.create_reaction_from_biota(rhea_rxn, e))
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

    def set_enzyme(self, enzyme_dict: EnzymeDict):
        """ Set enzyme """
        if not isinstance(enzyme_dict, dict):
            raise BadRequestException("The enzyme data must be a dictionary")
        self.enzyme = enzyme_dict

    def set_data(self, data: dict):
        """ Set data """
        if not isinstance(data, dict):
            raise BadRequestException("The data must be a dictionary")
        self.data = data

    # -- T --

    def to_str(self, show_ids=False) -> str:
        """
        Returns a string representation of the reaction

        :return: The string
        :rtype: `str`
        """

        _left = []
        _right = []
        _dir = {"L": " <==(E)== ", "R": " ==(E)==> ", "B": " <==(E)==> "}

        for comp_id, substrate in self.substrates.items():
            comp = substrate.compound
            stoich = substrate.stoich
            if show_ids:
                _id = comp.chebi_id if comp.chebi_id else comp.id
                _left.append(f"({stoich}) {_id}")
            else:
                _left.append(f"({stoich}) {comp.id}")

        for comp_id, product in self.products.items():
            comp = product.compound
            stoich = product.stoich
            if show_ids:
                _id = comp.chebi_id if comp.chebi_id else comp.id
                _right.append(f"({stoich}) {_id}")
            else:
                _right.append(f"({stoich}) {comp.id}")

        if not _left:
            _left = ["*"]

        if not _right:
            _right = ["*"]

        _str = " + ".join(_left) + \
            _dir[self.direction].replace("E", self.enzyme.get("ec_number", "")) + " + ".join(_right)
        # _str = _str + " " + str(self.enzyme)
        return _str
