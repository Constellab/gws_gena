# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
import json
import os
import re
import uuid
from typing import Dict, List, Optional, TypedDict

import numpy as np
from gws_biota import CompoundPosition as BiotaCompoundPosition
from gws_biota import EnzymeClass
from gws_biota import Taxonomy as BiotaTaxo
from gws_core import (BadRequestException, BoolParam, ConfigParams, DictRField,
                      File, JSONView, Logger, Resource, ResourceExporter,
                      RField, StrRField, Table, TabularView, UUIDRField,
                      resource_decorator, view)
from pandas import DataFrame

from .compound import Compound
from .reaction import Reaction
from .view.network_view import NetworkView

# ####################################################################
#
# Error classes
#
# ####################################################################


class NoCompartmentFound(BadRequestException):
    pass


class CompoundDuplicate(BadRequestException):
    pass


class ReactionDuplicate(BadRequestException):
    pass


NetworkReconTagDict = TypedDict("NetworkReconTagDict", {
    "reactions": dict,
    "compounds": dict
})

PositionDict = TypedDict("PositionDict", {
    "x": float,
    "y": float
})

CompoundDict = TypedDict("CompoundDict", {
    "id": str,
    "name": str,
    "charge": float,
    "mass": float,
    "monoisotopic_mass": float,
    "formula": str,
    "inchi": str,
    "compartment": str,
    "chebi_id": str,
    "alt_chebi_ids": list,
    "kegg_id": str,
    "inchikey": str,
    "position": PositionDict
})

ReactionDict = TypedDict("ReactionDict", {
    "id": str,
    "name": str,
    "direction": str,
    "lower_bound": float,
    "upper_bound": float,
    "rhea_id": str,
    "enzyme": dict,
    "position": PositionDict,
})

""" Tags generated during network reconstruction to annotated the reactions """
NetworkDict = TypedDict("NetworkDict", {
    "name": str,
    "metabolites": CompoundDict,
    "reactions": ReactionDict,
    "compartments": dict,
    "recon_tags": NetworkReconTagDict
})

# ####################################################################
#
# Network class
#
# ####################################################################


@resource_decorator("Network",
                    human_name="Network",
                    short_description="Metabolic network")
class Network(Resource):
    """
    Class that represents a network.

    A network is a collection of reconstructed metabolic pathways.
    """

    DEFAULT_NAME = "network"

    compounds: Dict[str, Compound] = DictRField()
    reactions: Dict[str, Reaction] = DictRField()
    compartments: Dict[str, str] = DictRField()

    _recon_tags: Dict[str, NetworkReconTagDict] = DictRField()
    _stats: Dict[str, str] = DictRField()
    _set_of_chebi_ids: Dict[str, str] = DictRField()
    _set_of_ec_numbers: Dict[str, str] = DictRField()
    _set_of_rhea_ids: Dict[str, str] = DictRField()

    def __init__(self):
        super().__init__()
        if not self.name:
            self.name = "Network"
            self.compounds = {}
            self.reactions = {}
            self.compartments = {}
            self._recon_tags = NetworkReconTagDict(reactions={}, compounds={})

    # -- A --

    def _add_compound(self, comp: Compound):
        """
        Adds a compound

        :param comp: The compound to add
        :type comp: `gena.network.Compound`
        """

        if not isinstance(comp, Compound):
            raise BadRequestException("The compound must an instance of Compound")
        if comp.id in self.compounds:
            raise CompoundDuplicate(f'Compound id "{comp.id}" is duplicated')
        if not comp.compartment:
            raise NoCompartmentFound("No compartment defined for the compound")
        if not comp.compartment in self.compartments:
            suffix = comp.compartment.split(Compound.COMPARTMENT_DELIMITER)[-1]
            self.compartments[comp.compartment] = Compound.COMPARTMENTS[suffix]["name"]

        self.compounds[comp.id] = comp
        self._stats = {}

        if comp.chebi_id:
            if comp.compartment not in self._set_of_chebi_ids:
                self._set_of_chebi_ids[comp.compartment] = {}
            self._set_of_chebi_ids[comp.compartment][comp.chebi_id] = comp.id
            for chebi_id in comp.alt_chebi_ids:
                self._set_of_chebi_ids[comp.compartment][chebi_id] = comp.id

    def add_reaction(self, rxn: Reaction):
        """
        Adds a product

        :param rxn: The reaction to add
        :type rxn: `gena.network.Reaction`
        """

        if not isinstance(rxn, Reaction):
            raise BadRequestException("The reaction must an instance of Reaction")
        if rxn.id in self.reactions:
            raise ReactionDuplicate(f"Reaction id {rxn.id} duplicate")

        # add reaction compounds to the network
        for sub in rxn.substrates.values():
            comp = sub["compound"]
            if not self.exists(comp):
                self._add_compound(comp)

        for prod in rxn.products.values():
            comp = prod["compound"]
            if not self.exists(comp):
                self._add_compound(comp)

        # add the reaction
        self.reactions[rxn.id] = rxn
        self._stats = {}

        if rxn.rhea_id:
            self._set_of_rhea_ids[rxn.rhea_id] = rxn.id
        if rxn.enzyme:
            ec = rxn.enzyme.get("ec_number")
            if ec:
                self._set_of_ec_numbers[ec] = rxn.id

    def update_reaction(self, rxn: Reaction):
        """ Update a reaction in the network """
        for sub in rxn.substrates.values():
            comp = sub["compound"]
            if not self.exists(comp):
                self._add_compound(comp)

        for prod in rxn.products.values():
            comp = prod["compound"]
            if not self.exists(comp):
                self._add_compound(comp)

    # -- B --

    # -- C --

    def copy(self) -> 'Network':
        net = Network()
        net.name = self.name
        net.compounds = copy.deepcopy(self.compounds)  # /!\ use deepcopy for performance
        net.reactions = copy.deepcopy(self.reactions)  # /!\ use deepcopy for performance
        net.compartments = self.compartments.copy()
        net._recon_tags = copy.deepcopy(self._recon_tags)
        net._stats = copy.deepcopy(self._stats)
        net._set_of_chebi_ids = copy.deepcopy(self._set_of_chebi_ids)
        net._set_of_ec_numbers = copy.deepcopy(self._set_of_ec_numbers)
        net._set_of_rhea_ids = copy.deepcopy(self._set_of_rhea_ids)
        return net

    def create_stoichiometric_matrix(self) -> DataFrame:
        rxn_ids = list(self.reactions.keys())
        comp_ids = list(self.compounds.keys())
        S = DataFrame(
            index=comp_ids,
            columns=rxn_ids,
            data=np.zeros((len(comp_ids), len(rxn_ids)))
        )

        for rxn_id in self.reactions:
            rxn = self.reactions[rxn_id]
            for comp_id in rxn._substrates:
                val = rxn._substrates[comp_id]["stoichiometry"]
                S.at[comp_id, rxn_id] -= val

            for comp_id in rxn._products:
                val = rxn._products[comp_id]["stoichiometry"]
                S.at[comp_id, rxn_id] += val

        return S

    def create_steady_stoichiometric_matrix(self, ignore_cofactors=False) -> DataFrame:
        S = self.create_stoichiometric_matrix()
        names = list(self.get_steady_compounds(ignore_cofactors=ignore_cofactors).keys())
        return S.loc[names, :]

    def create_non_steady_stoichiometric_matrix(self, include_biomass=True, ignore_cofactors=False) -> DataFrame:
        S = self.create_stoichiometric_matrix()
        names = list(self.get_non_steady_compounds(ignore_cofactors=ignore_cofactors).keys())
        return S.loc[names, :]

    def create_input_stoichiometric_matrix(self, include_biomass=True, ignore_cofactors=False) -> DataFrame:
        S = self.create_non_steady_stoichiometric_matrix(
            include_biomass=include_biomass,
            ignore_cofactors=ignore_cofactors
        )
        df = S.sum(axis=1)
        in_sub = df.loc[df < 0]
        names = in_sub.index.values
        return S.loc[names, :]

    def create_output_stoichiometric_matrix(self, include_biomass=True, ignore_cofactors=False) -> DataFrame:
        S = self.create_non_steady_stoichiometric_matrix(
            include_biomass=include_biomass,
            ignore_cofactors=ignore_cofactors
        )
        df = S.sum(axis=1)
        out_prod = df.loc[df > 0]
        names = out_prod.index.values
        return S.loc[names, :]

    # -- D --

    def dumps(self) -> NetworkDict:
        """
        Dumps the network
        """

        _met_json = []
        _rxn_json = []

        # switch all biomass compounds as majors
        biomass_comps = []
        biomass_rxn = self.get_biomass_reaction()
        if biomass_rxn is not None:
            for comp_id in biomass_rxn.substrates:
                biomass_comps.append(comp_id)
            for comp_id in biomass_rxn.products:
                biomass_comps.append(comp_id)

        for _met in self.compounds.values():

            # refresh position
            if _met.chebi_id:
                _met.position = BiotaCompoundPosition.get_by_chebi_id(
                    chebi_ids=[_met.chebi_id], compartment=_met.compartment)

            is_in_biomass_reaction = _met.id in biomass_comps
            _met_json.append({
                "id": _met.id,
                "name": _met.name,
                "charge": _met.charge,
                "mass": _met.mass,
                "monoisotopic_mass": _met.monoisotopic_mass,
                "formula": _met.formula,
                "inchi": _met.inchi,
                "is_cofactor": _met.is_cofactor,
                "level": _met.get_level(is_in_biomass_reaction=is_in_biomass_reaction),
                "compartment": _met.compartment,
                "chebi_id": _met.chebi_id,
                "kegg_id": _met.kegg_id,
                "position": {
                    "x": _met.position.x,
                    "y": _met.position.y
                }
            })

        for _rxn in self.reactions.values():
            _rxn_met = {}
            for sub in _rxn.substrates.values():
                comp_id = sub["compound"].id
                stoich = sub["stoichiometry"]
                _rxn_met.update({
                    comp_id: {
                        "stoich": -abs(stoich),
                        "points": _rxn.position.points.get(comp_id)
                    }
                })

            for prod in _rxn.products.values():
                comp_id = prod["compound"].id
                stoich = prod["stoichiometry"]
                _rxn_met.update({
                    prod["compound"].id: {
                        "stoich": abs(stoich),
                        "points": _rxn.position.points.get(comp_id)
                    }
                })

            _rxn_json.append({
                "id": _rxn.id,
                "name": _rxn.name,
                "enzyme": _rxn.enzyme,
                "rhea_id": _rxn.rhea_id,
                "metabolites": _rxn_met,
                "lower_bound": _rxn.lower_bound,
                "upper_bound": _rxn.upper_bound,
                "position": {
                    "x": _rxn.position.x,
                    "y": _rxn.position.y
                },
                "estimate": _rxn.estimate,
                "balance": _rxn.compute_mass_and_charge_balance()
            })

        _json = {
            "name": self.name,
            "metabolites": _met_json,
            "reactions": _rxn_json,
            "compartments": self.compartments,
            "recon_tags": self._recon_tags
        }

        return _json

    # -- E --

    def exists(self, elt: (Compound, Reaction)) -> bool:
        """
        Check that a compound or a reaction exists in the the network

        :param elt: The element (compound or reaction)
        :type elt: `gws.gena.Compound` or `gws.gena.Reaction`
        :return: True if the element exists, False otherwise
        :rtype: `bool`
        """

        if isinstance(elt, Reaction):
            return elt.id in self.reactions

        if isinstance(elt, Compound):
            return elt.id in self.compounds

        raise BadRequestException(
            "Invalid element. The element must be an instance of gws.gena.Compound or gws.gena.Reaction")

    # -- E --

    # -- F --

    # -- G --

    def get_compound_recon_tag(self, comp_id: str, tag_name: str = None):
        """
        Get a compound recon_tag value a compound id and a recon_tag name.

        :param comp_id: The compound id
        :type comp_id: `str`
        :param tag_name: The recon_tag name
        :type tag_name: `str`
        :return: The recon_tag value
        :rtype: `str`
        """

        if tag_name:
            return self.get_compound_recon_tags().get(comp_id, {}).get(tag_name)
        else:
            return self.get_compound_recon_tags().get(comp_id, {})

    def get_compound_recon_tags(self) -> dict:
        """
        Get all the compound recon_tags

        :return: The recon_tags
        :rtype: `dict`
        """

        return self._recon_tags["compounds"]

    def get_compound_ids(self) -> List[str]:
        return [comp_id for comp_id in self.compounds]

    def get_reaction_ids(self) -> List[str]:
        return [rxn_id for rxn_id in self.reactions]

    def get_reaction_recon_tag(self, rxn_id: str, tag_name: str = None):
        """
        Get a reaction tag value a compound id and a tag name.

        :param rxn_id: The reaction id
        :type rxn_id: `str`
        :param tag_name: The tag name
        :type tag_name: `str`
        :return: The recon_tag
        :rtype: `dict`
        """

        if tag_name:
            return self._recon_tags.get(rxn_id, {}).get(tag_name)
        else:
            return self._recon_tags.get(rxn_id, {})

    def get_compound_by_id(self, comp_id: str) -> Compound:
        """
        Get a compound by its id.

        :param comp_id: The compound id
        :type comp_id: `str`
        :return: The compound or `None` if the compond is not found
        :rtype: `gena.network.Compound` or `None`
        """

        return self.compounds.get(comp_id)

    def get_compounds_by_chebi_id(self, chebi_id: str, compartment: Optional[str] = None) -> List[Compound]:
        """
        Get a compound by its chebi id and compartment.

        :param chebi_id: The chebi id of the compound
        :type chebi_id: `str`
        :param compartment: The compartment of the compound
        :type compartment: `str`
        :return: The compound or `None` if the compond is not found
        :rtype: `gena.network.Compound` or `None`
        """

        if isinstance(chebi_id, float) or isinstance(chebi_id, int):
            chebi_id = f"CHEBI:{chebi_id}"

        if "CHEBI" not in chebi_id:
            chebi_id = f"CHEBI:{chebi_id}"

        if compartment:
            if compartment not in self._set_of_chebi_ids:
                return []
            c_id = self._set_of_chebi_ids[compartment].get(chebi_id)
            if c_id:
                return [self.compounds[c_id]]
            else:
                return []
        else:
            comps = []
            for d in self._set_of_chebi_ids.values():
                if chebi_id in d:
                    comp_id = d[chebi_id]
                    comps.append(self.compounds[comp_id])
            return comps

    def get_reaction_by_id(self, rxn_id: str) -> Reaction:
        """
        Get a reaction by its id.

        :param rxn_id: The reaction id
        :type rxn_id: `str`
        :return: The reaction or `None` if the reaction is not found
        :rtype: `gena.network.Reaction` or `None`
        """

        return self.reactions.get(rxn_id)

    def get_reaction_by_ec_number(self, ec_number: str) -> Reaction:
        """
        Get a reaction by its ec number.

        :param ec_number: The ec number of the reaction
        :type ec_number: `str`
        :return: The reaction or `None` if the reaction is not found
        :rtype: `gena.network.Reaction` or `None`
        """

        r_id = self._set_of_ec_numbers.get(ec_number)
        if r_id:
            return self.reactions[r_id]
        else:
            return None

    def get_reaction_by_rhea_id(self, rhea_id: str) -> Reaction:
        """
        Get a reaction by its rhea id.

        :param rhea_id: The rhea id of the reaction
        :type rhea_id: `str`
        :return: The reaction or `None` if the reaction is not found
        :rtype: `gena.network.Reaction` or `None`
        """

        r_id = self._set_of_rhea_ids.get(rhea_id)
        if r_id:
            return self.reactions[r_id]
        else:
            return None

    def get_reactions_related_to_chebi_id(self, chebi_id: str) -> List[Reaction]:
        rxns = []
        comps = self.get_compounds_by_chebi_id(chebi_id)
        if not comps:
            return rxns
        for rxn in self.reactions.values():
            for comp in comps:
                if comp.id in rxn.products or comp.id in rxn.substrates:
                    rxns.append(rxn)
        return rxns

    def _get_gap_info(self, gap_only=False) -> dict:
        """
        Get gap information
        """

        from ..recon.gap_finder import GapFinder
        return GapFinder.extract_gaps(self)

    def get_biomass_reaction(self) -> Reaction:
        """
        Get the biomass reaction if it exists

        :returns: The biomass reaction (or `None` if the biomass reaction does not exist)
        :rtype: `gena.network.Reaction` or `None`
        """

        for rxn in self.reactions.values():
            if rxn.is_biomass_reaction:
                return rxn

        # for k in self.reactions:
        #     if "biomass" in k.lower():
        #         return self.reactions[k]
        return None

    def get_biomass_compound(self) -> Compound:
        """
        Get the biomass compounds if it exists

        :returns: The biomass compounds
        :rtype: `gena.network.Compound`
        """

        for name in self.compounds:
            if self.compounds[name].is_biomass:
                return True
            # name_lower = name.lower()
            # if name_lower.endswith("_b") or name_lower == "biomass":
            #     return self.compounds[name]
        return None

    def get_compounds_by_compartments(self, compartment_list: List[str] = None) -> Dict[str, Compound]:
        """
        Get the compounds in a compartments

        :returns: The list of compounds
        :rtype: List[`gena.network.Compound`]
        """

        comps = {}
        for name in self.compounds:
            comp = self.compounds[name]
            if comp.compartment in compartment_list:
                comps[name] = self.compounds[name]
        return comps

    def get_steady_compounds(self, ignore_cofactors=False) -> Dict[str, Compound]:
        """
        Get the steady compounds

        :returns: The list of steady compounds
        :rtype: List[`gena.network.Compound`]
        """

        comps = {}
        for id in self.compounds:
            comp = self.compounds[id]
            if comp.is_steady:
                if ignore_cofactors and comp.is_cofactor:
                    continue
                else:
                    comps[id] = self.compounds[id]
        return comps

    def get_non_steady_compounds(self, ignore_cofactors=False) -> Dict[str, Compound]:
        """
        Get the non-steady compounds

        :returns: The list of non-steady compounds
        :rtype: List[`gena.network.Compound`]
        """

        comps = {}
        for id in self.compounds:
            comp = self.compounds[id]
            if not comp.is_steady:
                if ignore_cofactors and comp.is_cofactor:
                    continue
                else:
                    comps[id] = self.compounds[id]
        return comps

    def get_reaction_bounds(self) -> DataFrame:
        """
        Get the reaction bounds `[lb, ub]`

        :return: The reaction bounds
        :rtype: `DataFrame`
        """

        bounds = DataFrame(
            index=self.get_reaction_ids(),
            columns=["lb", "ub"],
            data=np.zeros((len(self.reactions), 2))
        )
        for k in self.reactions:
            rxn: Reaction = self.reactions[k]
            bounds.loc[k, :] = [rxn.lower_bound, rxn.upper_bound]
        return bounds

    def get_number_of_reactions(self) -> int:
        return len(self.reactions)

    def get_number_of_compounds(self) -> int:
        return len(self.compounds)

    # -- H --

    def has_sink(self) -> bool:
        for k in self.compounds:
            comp: Compound = self.compounds[k]
            if comp.is_sink:
                return True

    # -- I --

    # -- L --

    @ classmethod
    def loads(cls, data: NetworkDict, skip_bigg_exchange_reactions: bool = True, loads_biota_info: bool = False,
              biomass_reaction_id: str = None) -> 'Network':
        """ Loads JSON data and create a Network  """

        if not data.get("compartments"):
            raise BadRequestException("Invalid network dump. Compartments not found")
        if not data.get("metabolites"):
            raise BadRequestException("Invalid network dump. Metabolites not found")
        if not data.get("reactions"):
            raise BadRequestException("Invalid network dump. Reactions not found")

        net = Network()
        net.name = data.get("name", cls.DEFAULT_NAME)
        net.compartments = data["compartments"]

        ckey = "compounds" if "compounds" in data else "metabolites"

        added_comps = {}
        for val in data[ckey]:
            compart = val["compartment"]
            if not compart in net.compartments:
                raise BadRequestException(
                    f"The compartment '{compart}' of the compound '{val['id']}' not declared in the lists of compartments")

            chebi_id = val.get("chebi_id", "")
            inchikey = val.get("inchikey", "")
            is_bigg_data_format = ("annotation" in val)

            alt_chebi_ids = []
            if not chebi_id and not inchikey and is_bigg_data_format:
                annotation = val["annotation"]
                alt_chebi_ids = annotation.get("chebi", [])
                inchikey = annotation.get("inchi_key", [""])[0]
                if alt_chebi_ids:
                    chebi_id = alt_chebi_ids.pop(0)

            comp_id = val["id"]  # .replace(self.Compound.FLATTENING_DELIMITER,Compound.COMPARTMENT_DELIMITER)
            comp = None

            if loads_biota_info:
                if chebi_id or inchikey:
                    try:
                        comp = Compound.from_biota(
                            id=comp_id,
                            name=val.get("name", ""),
                            chebi_id=chebi_id,
                            inchikey=inchikey,
                            compartment=compart,
                        )
                    except Exception as _:
                        pass

            if comp is None:
                comp = Compound(
                    id=comp_id,
                    name=val.get("name", ""),
                    compartment=compart,
                    charge=val.get("charge", ""),
                    mass=val.get("mass", ""),
                    monoisotopic_mass=val.get("monoisotopic_mass", ""),
                    formula=val.get("formula", ""),
                    inchi=val.get("inchi", ""),
                    inchikey=val.get("inchikey", ""),
                    chebi_id=chebi_id,
                    alt_chebi_ids=alt_chebi_ids,
                    kegg_id=val.get("kegg_id", "")
                )

            if alt_chebi_ids:
                comp.alt_chebi_ids = alt_chebi_ids

            position = val.get("position", {})
            if position:
                comp.position.x = position.get("x", None)
                comp.position.y = position.get("y", None)
                comp.position.z = position.get("z", None)

            added_comps[comp_id] = comp

        for val in data["reactions"]:
            if is_bigg_data_format and skip_bigg_exchange_reactions and val["id"].startswith("EX_"):
                continue

            rxn = Reaction(
                id=val["id"],  # .replace(self.Compound.FLATTENING_DELIMITER,Compound.COMPARTMENT_DELIMITER),\
                name=val.get("name"), \
                lower_bound=val.get("lower_bound", Reaction.lower_bound), \
                upper_bound=val.get("upper_bound", Reaction.upper_bound), \
                enzyme=val.get("enzyme", {}),\
                direction=val.get("direction", "B"),\
                rhea_id=val.get("rhea_id", "")\
            )

            position = val.get("position", {})
            if position:
                rxn.position.x = position.get("x", None)
                rxn.position.y = position.get("y", None)
                rxn.position.z = position.get("z", None)

            rxn.position.points = {}
            if val.get("estimate"):
                rxn.set_estimate(val.get("estimate"))

            reg_exp = re.compile(r"CHEBI\:\d+$")
            for comp_id in val[ckey]:
                comp = added_comps[comp_id]
                # search according to compound ids
                # if re.match(r"CHEBI\:\d+$", comp_id):
                if reg_exp.match(comp_id):
                    comps = net.get_compounds_by_chebi_id(comp_id)
                    # select the compound in the good compartment
                    for c in comps:
                        if c.compartment == comp.compartment:
                            break

                if isinstance(val[ckey][comp_id], dict):
                    stoich = float(val[ckey][comp_id].get("stoich"))
                    points = val[ckey][comp_id].get("points")
                else:
                    stoich = float(val[ckey][comp_id])  # for retro compatiblity
                    points = None
                if stoich < 0:
                    rxn.add_substrate(comp, stoich)
                elif stoich > 0:
                    rxn.add_product(comp, stoich)

                rxn.position.points[comp.id] = points

            net.add_reaction(rxn)

        # check if the biomass comaprtment exists
        biomass_compartment: str = Compound.COMPARTMENT_BIOMASS
        if net.get_biomass_compound() is None:
            Logger.warning("No biomass compound found. Try creating a dummy biomass compound.")
            if biomass_reaction_id:
                if biomass_reaction_id in net.reactions:
                    rxn = net.reactions[biomass_reaction_id]
                    biomass = Compound(name="Biomass", compartment=biomass_compartment)
                    rxn.add_product(biomass, 1)
                    #net.compartments[biomass_compartment] = Compound.COMPARTMENTS[biomass_compartment]
                    net.compartments[biomass_compartment] = Compound.COMPARTMENTS[biomass_compartment]["name"]
                    net.update_reaction(rxn)
                else:
                    raise BadRequestException(f"No reaction found with id '{biomass_reaction_id}'.")
            else:
                for rxn in net.reactions.values():
                    if "biomass" in rxn.id.lower():
                        biomass = Compound(name="Biomass", compartment=biomass_compartment)
                        rxn.add_product(biomass, 1)
                        #net.compartments[biomass_compartment] = Compound.COMPARTMENT_BIOMASS
                        net.compartments[biomass_compartment] = Compound.COMPARTMENTS[biomass_compartment]["name"]
                        net.update_reaction(rxn)
                        Logger.warning(
                            f"The reaction '{rxn.name}' was automatically infered as biomass reaction.")
                        break

        return net

    # -- N --

    # -- P --

    # -- R --

    def remove_reaction(self, rxn_id: str):
        """
        Remove a reaction from the network

        :param rxn_id: The id of the reaction to remove
        :type rxn_id: `str`
        """

        if not isinstance(rxn_id, str):
            raise BadRequestException("The reaction id must be a string")

        del self.reactions[rxn_id]

    def get_compound_stats_as_json(self, **kwargs) -> dict:
        return self.stats["compounds"]

    def get_compound_stats_as_table(self) -> Table:
        _dict = self.stats["compounds"]
        for comp_id in _dict:
            _dict[comp_id]["chebi_id"] = self.compounds[comp_id].chebi_id
        df = DataFrame.from_dict(_dict, columns=["count", "frequency", "chebi_id"], orient="index")
        df = df.sort_values(by=['frequency'], ascending=False)
        return Table(data=df)

    def get_gaps_as_table(self) -> Table:
        _dict = self._get_gap_info()
        df = DataFrame.from_dict(_dict, columns=["is_substrate", "is_product", "is_gap"], orient="index")
        return Table(data=df)

    def get_gaps_as_json(self) -> Table:
        df = self._get_gap_info()
        return Table(data=df)

    def get_total_abs_flux_as_table(self) -> Table:
        total_flux = 0
        for k in self.reactions:
            rxn = self.reactions[k]
            if rxn._estimate:
                total_flux += abs(rxn.estimate["value"])
        df = DataFrame.from_dict({"0": [total_flux]}, columns=["total_abs_flux"], orient="index")
        return Table(data=df)

    def get_stats_as_json(self) -> dict:
        return self.stats

    # -- R --

    # -- S --

    @property
    def stats(self) -> dict:
        if self._stats:
            return self._stats
        stats = {
            "compound_count": len(self.compounds),
            "reaction_count": len(self.reactions),
            "compounds": {},
            "reactions": {}
        }
        for comp_id in self.compounds:
            stats["compounds"][comp_id] = {
                "count": 0
            }
        for rxn_id in self.reactions:
            rxn = self.reactions[rxn_id]
            for comp_id in rxn.products:
                stats["compounds"][comp_id]["count"] += 1
            for comp_id in rxn.substrates:
                stats["compounds"][comp_id]["count"] += 1
        if stats["compound_count"]:
            for comp_id in self.compounds:
                stats["compounds"][comp_id]["freq"] = stats["compounds"][comp_id]["count"] / stats["compound_count"]
        self._stats = stats
        return stats

    def set_reaction_recon_tag(self, tag_id, tag: dict):
        if not isinstance(tag, dict):
            raise BadRequestException("The tag must be a dictionary")
        if not tag_id in self._recon_tags["reactions"]:
            self._recon_tags["reactions"][tag_id] = {}
        self._recon_tags["reactions"][tag_id].update(tag)

    def set_compound_recon_tag(self, tag_id, tag: dict):
        if not isinstance(tag, dict):
            raise BadRequestException("The tag must be a dictionary")
        if not tag_id in self._recon_tags["compounds"]:
            self._recon_tags["compounds"][tag_id] = {}
        self._recon_tags["compounds"][tag_id].update(tag)

    # -- T --

    def to_str(self) -> str:
        """
        Returns a string representation of the network

        :rtype: `str`
        """

        _str = ""
        for rxn_id in self.reactions:
            _str += "\n" + self.reactions[rxn_id].to_str()
        return _str

    def to_csv(self) -> str:
        """
        Returns a CSV representation of the network

        :rtype: `str`
        """

        return self.to_dataframe().to_csv()

    def to_table(self) -> Table:
        return Table(data=self.to_dataframe())

    def to_dataframe(self) -> DataFrame:
        """
        Returns a DataFrame representation of the network
        """

        bkms = ['brenda', 'kegg', 'metacyc']
        column_names = [
            "id",
            "equation_str",
            "enzyme",
            "ec_number",
            "lb",
            "ub",
            "enzyme_class",
            "is_from_gap_filling",
            "comments",
            "substrates",
            "products",
            "mass_balance",
            "charge_balance",
            *BiotaTaxo._tax_tree,
            *bkms
        ]
        rxn_row = {}
        for k in column_names:
            rxn_row[k] = ""

        data = []
        rxn_count = 1
        for k in self.reactions:
            rxn = self.reactions[k]
            enz = ""
            ec = ""
            comment = []
            enzyme_class = ""
            is_from_gap_filling = False
            pathway_cols = {}
            for f in bkms:
                pathway_cols[f] = ""

            tax_cols = {}
            for f in BiotaTaxo._tax_tree:
                tax_cols[f] = ""

            flag = self.get_reaction_recon_tag(rxn.id, "is_from_gap_filling")
            if flag:
                is_from_gap_filling = True
            if rxn.enzyme:
                enz = rxn.enzyme.get("name", "--")
                ec = rxn.enzyme.get("ec_number", "--")
                deprecated_enz = rxn.enzyme.get("related_deprecated_enzyme")
                if deprecated_enz:
                    comment.append(deprecated_enz["ec_number"] + " (" + deprecated_enz["reason"] + ")")
                if rxn.enzyme.get("pathways"):
                    bkms = ['brenda', 'kegg', 'metacyc']
                    pw = rxn.enzyme.get("pathways")
                    if pw:
                        for db in bkms:
                            if pw.get(db):
                                pathway_cols[db] = pw[db]["name"] + " (" + (pw[db]
                                                                            ["id"] if pw[db]["id"] else "--") + ")"
                if rxn.enzyme.get("tax"):
                    tax = rxn.enzyme.get("tax")
                    for f in BiotaTaxo._tax_tree:
                        if f in tax:
                            tax_cols[f] = tax[f]["name"] + " (" + str(tax[f]["tax_id"]) + ")"
                if rxn.enzyme.get("ec_number"):
                    try:
                        enzyme_class = EnzymeClass.get(EnzymeClass.ec_numbner == rxn.enzyme.get("ec_number"))
                    except Exception as _:
                        pass
            subs = []
            for m in rxn.substrates:
                c = rxn.substrates[m]["compound"]
                subs.append(c.name + " (" + c.chebi_id + ")")
            prods = []
            for m in rxn.products:
                c = rxn.products[m]["compound"]
                prods.append(c.name + " (" + c.chebi_id + ")")
            if not subs:
                subs = ["*"]
            if not prods:
                prods = ["*"]

            balance = rxn.compute_mass_and_charge_balance()
            _rxn_row = rxn_row.copy()
            _rxn_row["id"] = rxn.id
            _rxn_row["equation_str"] = rxn.to_str()
            _rxn_row["enzyme"] = enz
            _rxn_row["ec_number"] = ec
            _rxn_row["ub"] = str(rxn.lower_bound)
            _rxn_row["lb"] = str(rxn.upper_bound)
            _rxn_row["enzyme_class"] = enzyme_class
            _rxn_row["is_from_gap_filling"] = is_from_gap_filling
            _rxn_row["comments"] = "; ".join(comment)
            _rxn_row["substrates"] = "; ".join(subs)
            _rxn_row["products"] = "; ".join(prods)
            _rxn_row["mass_balance"] = balance["mass"]
            _rxn_row["charge_balance"] = balance["charge"]
            _rxn_row = {**_rxn_row, **tax_cols, **pathway_cols}
            rxn_count += 1
            data.append(list(_rxn_row.values()))

        # add the errored ec numbers
        for k in self._recon_tags:
            t = self._recon_tags[k]
            ec = t.get("ec_number")
            is_partial_ec_number = t.get("is_partial_ec_number")
            error = t.get("error")
            if not ec:
                continue
            _rxn_row = rxn_row.copy()
            _rxn_row["ec_number"] = ec       # ec number
            _rxn_row["comments"] = error     # comment
            if is_partial_ec_number:
                try:
                    enzyme_class = EnzymeClass.get(EnzymeClass.ec_number == ec)
                    _rxn_row["enzyme_class"] = enzyme_class.get_name()
                except Exception as _:
                    pass
            rxn_count += 1
            data.append(list(_rxn_row.values()))

        # export
        data = DataFrame(data, columns=column_names)
        data = data.sort_values(by=['id'])
        return data

    # -- V --

    @view(view_type=NetworkView, human_name="Network",
          specs={
              "remove_blocked":
              BoolParam(
                  default_value=False, optional=True, human_name="Remove blocked reactions",
                  short_description="Set True to remove blocked reactions; False otherwise"),
          })
    def view_as_network(self, params: ConfigParams) -> NetworkView:
        return NetworkView(data=self)

    @view(view_type=JSONView, default_view=True, human_name="Summary")
    def view_as_summary(self, params: ConfigParams) -> JSONView:
        biomass_rxn = self.get_biomass_reaction()

        data = {
            "Name": self.name,
            "Number of reactions": len(self.reactions),
            "Number of metabolites": len(self.compounds),
            "Number of compartments": len(self.compartments),
            "Compartments": [c for c in self.compartments.values()]
        }

        if biomass_rxn:
            data["Biomass reaction"] = {
                "ID": biomass_rxn.id,
                "Name": biomass_rxn.name,
                "Formula": [biomass_rxn.to_str()],
                "Flux estimate": biomass_rxn.estimate
            }
        else:
            data["Biomass reaction"] = {}

        j_view = JSONView()
        j_view.set_data(data=data)
        return j_view

    @ view(view_type=TabularView, human_name="Reaction table")
    def view_as_table(self, params: ConfigParams) -> TabularView:
        t_view = TabularView()
        t_view.set_data(data=self.to_dataframe())
        return t_view

    @ view(view_type=JSONView, human_name="JSON view")
    def view_as_json(self, params: ConfigParams) -> JSONView:
        json_view: JSONView = super().view_as_json(params)
        json_view.set_data(self.dumps())
        return json_view

    @ view(view_type=TabularView, human_name="Reaction gaps")
    def view_gaps_as_table(self, params: ConfigParams) -> TabularView:
        table: Table = self.get_gaps_as_table()
        t_view = TabularView()
        t_view.set_data(data=table.to_dataframe())
        return t_view

    @ view(view_type=TabularView, human_name="Compound distrib.")
    def view_compound_stats_as_table(self, params: ConfigParams) -> TabularView:
        table: Table = self.get_compound_stats_as_table()
        t_view = TabularView()
        t_view.set_data(data=table.to_dataframe())
        return t_view
