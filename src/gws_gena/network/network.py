# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
import json
import os
import re
import uuid
from typing import Dict, List, Optional, TypedDict, Union

import numpy as np
from gws_biota import CompoundLayoutDict as BiotaCompoundLayoutDict
from gws_biota import EnzymeClass
from gws_biota import ReactionLayoutDict as BiotaReactionLayoutDict
from gws_biota import Taxonomy as BiotaTaxo
from gws_core import (BadRequestException, BoolParam, ConfigParams, DictRField,
                      File, JSONView, Logger, Resource, ResourceExporter,
                      RField, StrRField, Table, TabularView, UUIDRField,
                      resource_decorator, view)
from pandas import DataFrame

from .compartment import Compartment
from .compound import Compound
from .helper.network_loader_helper import NetworkLoaderHelper
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

ReactionPositionDict = TypedDict("ReactionPositionDict", {
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
    "layout": BiotaCompoundLayoutDict
})

ReactionDict = TypedDict("ReactionDict", {
    "id": str,
    "name": str,
    "direction": str,
    "lower_bound": float,
    "upper_bound": float,
    "rhea_id": str,
    "enzyme": dict,
    "layout": BiotaReactionLayoutDict,
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

    def add_compound(self, comp: Compound):
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
            suffix = comp.compartment.split(Compartment.DELIMITER)[-1]
            self.compartments[comp.compartment] = Compartment.COMPARTMENTS[suffix]["name"]

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
            if not self.compound_exists(comp):
                self.add_compound(comp)

        for prod in rxn.products.values():
            comp = prod["compound"]
            if not self.compound_exists(comp):
                self.add_compound(comp)

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
            if not self.compound_exists(comp):
                self.add_compound(comp)

        for prod in rxn.products.values():
            comp = prod["compound"]
            if not self.compound_exists(comp):
                self.add_compound(comp)

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
        """
        Create the full stoichiometric matrix of the network
        """
        rxn_ids = list(self.reactions.keys())
        comp_ids = list(self.compounds.keys())
        S = DataFrame(
            index=comp_ids,
            columns=rxn_ids,
            data=np.zeros((len(comp_ids), len(rxn_ids)))
        )

        for rxn_id in self.reactions:
            rxn = self.reactions[rxn_id]
            for comp_id in rxn.substrates:
                val = rxn.substrates[comp_id]["stoichiometry"]
                S.at[comp_id, rxn_id] -= val

            for comp_id in rxn.products:
                val = rxn.products[comp_id]["stoichiometry"]
                S.at[comp_id, rxn_id] += val

        return S

    def create_steady_stoichiometric_matrix(self, ignore_cofactors=False) -> DataFrame:
        """
        Create the steady stoichiometric matrix of the network

        We define by steady stoichiometric matrix, the submatrix of the stoichimetric matrix
        involving the steady compounds (e.g. intra-cellular compounds)
        """

        S = self.create_stoichiometric_matrix()
        names = list(self.get_steady_compounds(ignore_cofactors=ignore_cofactors).keys())
        return S.loc[names, :]

    def create_non_steady_stoichiometric_matrix(self, include_biomass=True, ignore_cofactors=False) -> DataFrame:
        """
        Create the non-steady stoichiometric matrix of the network

        We define by non-steady stoichiometric matrix, the submatrix of the stoichimetric matrix
        involving the non-steady compounds (e.g. extra-cellular, biomass compounds)
        """

        S = self.create_stoichiometric_matrix()
        names = list(self.get_non_steady_compounds(ignore_cofactors=ignore_cofactors).keys())
        return S.loc[names, :]

    def create_input_stoichiometric_matrix(self, include_biomass=True, ignore_cofactors=False) -> DataFrame:
        """
        Create the input stoichiometric matrix of the network

        We define by input stoichiometric matrix, the submatrix of the stoichimetric matrix
        involving the consumed compounds
        """

        S = self.create_non_steady_stoichiometric_matrix(
            include_biomass=include_biomass,
            ignore_cofactors=ignore_cofactors
        )
        df = S.sum(axis=1)
        in_sub = df.loc[df < 0]
        names = in_sub.index.values
        return S.loc[names, :]

    def create_output_stoichiometric_matrix(self, include_biomass=True, ignore_cofactors=False) -> DataFrame:
        """
        Create the output stoichiometric matrix of the network

        We define by input stoichiometric matrix, the submatrix of the stoichimetric matrix
        involving the excreted compounds
        """

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
                comp = self.compounds[comp_id]
                biomass_comps.append(comp_id)
                comp.append_biomass_layout()
            for comp_id in biomass_rxn.products:
                comp = self.compounds[comp_id]
                biomass_comps.append(comp_id)
                if not comp.is_biomass():
                    comp.append_biomass_layout()

        for _met in self.compounds.values():
            _met_json.append({
                "id": _met.id,
                "name": _met.name,
                "charge": _met.charge,
                "mass": _met.mass,
                "monoisotopic_mass": _met.monoisotopic_mass,
                "formula": _met.formula,
                "inchi": _met.inchi,
                "is_cofactor": _met.is_cofactor(),
                "level": _met.get_level(),
                "compartment": _met.compartment,
                "chebi_id": _met.chebi_id,
                "kegg_id": _met.kegg_id,
                "layout": _met.layout,
            })

        for _rxn in self.reactions.values():
            _rxn_met = {}
            for sub in _rxn.substrates.values():
                comp_id = sub["compound"].id
                stoich = sub["stoichiometry"]
                _rxn_met.update({
                    comp_id: {
                        "stoich": -abs(stoich),
                    }
                })

            for prod in _rxn.products.values():
                comp_id = prod["compound"].id
                stoich = prod["stoichiometry"]
                _rxn_met.update({
                    prod["compound"].id: {
                        "stoich": abs(stoich),
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
                "layout": {"x": None, "y": None},
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

    def compound_exists(self, comp: Compound) -> bool:
        """
        Check that a compound exists in the network

        :param rxn: The compound
        :type rxn: `gws.gena.Compound`
        :return: True if the compound exists, False otherwise
        :rtype: `bool`
        """

        if not isinstance(comp, Compound):
            raise BadRequestException("The reaction must be an instance of Reaction")

        return comp.id in self.compounds

    def reaction_exists(self, rxn: Reaction) -> bool:
        """
        Check that a reaction exists in the network

        :param rxn: The reaction
        :type rxn: `gws.gena.Reaction`
        :return: True if the reaction exists, False otherwise
        :rtype: `bool`
        """

        if not isinstance(rxn, Reaction):
            raise BadRequestException("The reaction must be an instance of Reaction")

        return rxn.id in self.reactions

    # -- E --

    # -- F --

    def flatten_reaction_id(self, rxn: Reaction) -> str:
        """ Flatten the id of a reaction """
        if not isinstance(rxn, Reaction):
            raise BadRequestException("The reaction must be an instance of Reaction")
        if not self.reaction_exists(rxn):
            raise BadRequestException(f"The reaction {rxn.id} does not exist in the network")
        return rxn.flatten_id(rxn.id, self.name)

    def flatten_compound_id(self, comp: Compound) -> str:
        """ Flatten the id of a compound """
        if not isinstance(comp, Compound):
            raise BadRequestException("The compound must be an instance of Compound")
        if not self.compound_exists(comp):
            raise BadRequestException(f"The reaction {comp.id} does not exist in the network")
        return comp.flatten_id(comp.id, self.name)

    def get_gaps(self) -> dict:
        """
        Get gap information
        """

        from .helper.gap_finder_helper import GapFinderHelper
        return GapFinderHelper.find(self)

    def get_orphan_compound_ids(self) -> List[str]:
        """ Get the ids of orphan compounds """
        from .helper.deadend_finder_helper import DeadendFinderHelper
        df = DeadendFinderHelper.find(self)
        comp_ids = [idx for idx in df.index if df.at[idx, "is_orphan"]]
        return comp_ids

    def get_deadend_compound_ids(self) -> List[str]:
        """ Get the ids of dead-end compounds """
        from .helper.deadend_finder_helper import DeadendFinderHelper
        df = DeadendFinderHelper.find(self)
        comp_ids = [idx for idx in df.index if df.at[idx, "is_dead_end"]]
        return comp_ids

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
        return list(self.compounds.keys())

    def get_reaction_ids(self) -> List[str]:
        return list(self.reactions.keys())

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
        """ Get the reactions related to a compound with having a given CheBI ID """
        rxns = []
        comps = self.get_compounds_by_chebi_id(chebi_id)
        if not comps:
            return rxns
        for rxn in self.reactions.values():
            for comp in comps:
                if comp.id in rxn.products or comp.id in rxn.substrates:
                    rxns.append(rxn)
        return rxns

    def get_biomass_reaction(self) -> Reaction:
        """
        Get the biomass reaction if it exists

        :returns: The biomass reaction (or `None` if the biomass reaction does not exist)
        :rtype: `gena.network.Reaction` or `None`
        """

        for rxn in self.reactions.values():
            if rxn.is_biomass_reaction():
                return rxn
        return None

    def get_biomass_compound(self) -> Compound:
        """
        Get the biomass compounds if it exists

        :returns: The biomass compounds
        :rtype: `gena.network.Compound`
        """

        for comp in self.compounds.values():
            if comp.is_biomass():
                return True
        return None

    def get_compounds_by_compartments(self, compartment_list: List[str] = None) -> Dict[str, Compound]:
        """
        Get the compounds in a compartments

        :returns: The list of compounds
        :rtype: List[`gena.network.Compound`]
        """

        comps = {}
        for comp_id in self.compounds:
            comp = self.compounds[comp_id]
            if comp.compartment in compartment_list:
                comps[comp_id] = self.compounds[comp_id]
        return comps

    def get_steady_compounds(self, ignore_cofactors=False) -> Dict[str, Compound]:
        """
        Get the steady compounds

        :returns: The list of steady compounds
        :rtype: List[`gena.network.Compound`]
        """

        comps = {}
        for comp_id in self.compounds:
            comp = self.compounds[comp_id]
            if comp.is_steady():
                if ignore_cofactors and comp.is_cofactor():
                    continue
                else:
                    comps[comp_id] = self.compounds[comp_id]
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
            if not comp.is_steady():
                if ignore_cofactors and comp.is_cofactor():
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
            if comp.is_sink():
                return True

    # -- I --

    # -- L --

    @ classmethod
    def loads(cls, data: NetworkDict, *, skip_bigg_exchange_reactions: bool = True, loads_biota_info: bool = False,
              biomass_reaction_id: str = None, skip_orphans: bool = False) -> 'Network':
        """ Load JSON data and create a Network  """

        if not data.get("compartments"):
            raise BadRequestException("Invalid network dump. Compartments not found")
        if not data.get("metabolites"):
            raise BadRequestException("Invalid network dump. Metabolites not found")
        if not data.get("reactions"):
            raise BadRequestException("Invalid network dump. Reactions not found")

        return NetworkLoaderHelper.loads(
            data,
            skip_bigg_exchange_reactions=skip_bigg_exchange_reactions,
            loads_biota_info=loads_biota_info,
            biomass_reaction_id=biomass_reaction_id,
            skip_orphans=skip_orphans
        )

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
        """ Get compound stats as JSON """
        return self.stats["compounds"]

    def get_compound_stats_as_table(self) -> Table:
        """ Get compound stats as table """
        _dict = self.stats["compounds"]
        for comp_id in _dict:
            _dict[comp_id]["chebi_id"] = self.compounds[comp_id].chebi_id
        df = DataFrame.from_dict(_dict, columns=["count", "frequency", "chebi_id"], orient="index")
        df = df.sort_values(by=['frequency'], ascending=False)
        return Table(data=df)

    def get_gaps_as_table(self) -> Table:
        """ Get gaps as table """
        _dict = self.get_gaps()
        df = DataFrame.from_dict(_dict, columns=["name", "is_substrate", "is_product",
                                 "is_dead_end", "is_orphand"], orient="index")
        return Table(data=df)

    def get_gaps_as_json(self) -> Table:
        """ Get gaps as JSON """
        df = self.get_gaps()
        return Table(data=df)

    def get_total_abs_flux_as_table(self) -> Table:
        """ Get the total absolute flux as table """
        total_flux = 0
        for k in self.reactions:
            rxn = self.reactions[k]
            if rxn.estimate:
                total_flux += abs(rxn.estimate["value"])
        df = DataFrame.from_dict({"0": [total_flux]}, columns=["total_abs_flux"], orient="index")
        return Table(data=df)

    def get_stats_as_json(self) -> dict:
        """ Get stats as JSON """
        return self.stats

    # -- R --

    # -- S --

    @property
    def stats(self) -> dict:
        """ Gather and return networks stats """
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
        """ Set a reaction recon tag """
        if not isinstance(tag, dict):
            raise BadRequestException("The tag must be a dictionary")
        if not tag_id in self._recon_tags["reactions"]:
            self._recon_tags["reactions"][tag_id] = {}
        self._recon_tags["reactions"][tag_id].update(tag)

    def set_compound_recon_tag(self, tag_id, tag: dict):
        """ Set a compound recon tag """
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
            *BiotaTaxo.get_tax_tree(),
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
            for f in BiotaTaxo.get_tax_tree():
                tax_cols[f] = ""

            flag = self.get_reaction_recon_tag(rxn.id, "is_from_gap_filling")
            if flag:
                is_from_gap_filling = True
            if rxn.enzyme:
                enz = rxn.enzyme.get("name", "--")
                ec = rxn.enzyme.get("ec_number", "--")
                deprecated_enz = rxn.enzyme.get("related_deprecated_enzyme")
                if deprecated_enz:
                    comment.append(str(deprecated_enz["ec_number"]) + " (" + str(deprecated_enz["reason"]) + ")")
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
                    for f in BiotaTaxo.get_tax_tree():
                        if f in tax:
                            tax_cols[f] = tax[f]["name"] + " (" + str(tax[f]["tax_id"]) + ")"
                if rxn.enzyme.get("ec_number"):
                    enzyme_class = EnzymeClass.get_or_none(EnzymeClass.ec_number == rxn.enzyme.get("ec_number"))
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
                enzyme_class = EnzymeClass.get_or_none(EnzymeClass.ec_number == ec)
                if enzyme_class is not None:
                    _rxn_row["enzyme_class"] = enzyme_class.get_name()
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

    def get_summary(self) -> dict:
        """ Return the summary of the network """
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

        return data

    @view(view_type=JSONView, default_view=True, human_name="Summary")
    def view_as_summary(self, params: ConfigParams) -> JSONView:
        """ Return the summary View of the network """
        data = self.get_summary()
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
