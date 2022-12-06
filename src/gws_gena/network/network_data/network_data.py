# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
import json
import os
import re
import uuid
from typing import Any, Dict, List, Optional, TypedDict, Union

import numpy as np
from gws_biota import CompoundLayout as BiotaCompoundLayout
from gws_biota import CompoundLayoutDict as BiotaCompoundLayoutDict
from gws_biota import EnzymeClass
from gws_biota import ReactionLayoutDict as BiotaReactionLayoutDict
from gws_biota import Taxonomy as BiotaTaxo
from gws_core import (BadRequestException, BoolParam, ConfigParams, DictRField,
                      File, JSONView, Logger, Resource, ResourceExporter,
                      RField, SerializableObjectJson, SerializableRField,
                      StrRField, Table, TableView, Task, UUIDRField,
                      resource_decorator, view)
from pandas import DataFrame

from ..compartment.compartment import Compartment
from ..compound.compound import Compound
from ..exceptions.compartment_exceptions import NoCompartmentFound
from ..exceptions.compound_exceptions import CompoundDuplicate
from ..exceptions.reaction_exceptions import ReactionDuplicate
from ..helper.slugify_helper import SlugifyHelper
from ..reaction.reaction import Reaction
from ..typing.network_typing import NetworkDict, NetworkReconTagDict
from ..typing.simulation_typing import SimulationDict
from .helper.network_data_dumper_helper import NetworkDataDumperHelper
from .helper.network_data_loader_helper import NetworkDataLoaderHelper


class NetworkData(SerializableObjectJson):
    """
    Class that represents a network.

    A network is a collection of reconstructed metabolic pathways.
    """

    DEFAULT_NAME = "network"
    DELIMITER = "_"

    name: str = None
    compounds: Dict[str, Compound] = None
    reactions: Dict[str, Reaction] = None
    compartments: Dict[str, Compartment] = None
    simulations: Dict[str, SimulationDict] = None
    recon_tags: Dict[str, NetworkReconTagDict] = None

    # created by the class
    _compartment_chebi_ids: Dict[str, str] = None
    _ec_rxn_ids_map: Dict[str, str] = None
    _rhea_rxn_ids_map: Dict[str, str] = None

    def __init__(self):
        super().__init__()
        if not self.name:
            self.name = self.DEFAULT_NAME
            self.compounds = {}
            self.reactions = {}
            self.compartments = {}
            self.simulations = {}
            self.recon_tags = NetworkReconTagDict(reactions={}, compounds={})

            self._compartment_chebi_ids = {}
            self._ec_rxn_ids_map = {}
            self._rhea_rxn_ids_map = {}

    def serialize(self) -> NetworkDict:
        """
        Serialize
        """

        return self.dumps()

    @ classmethod
    def deserialize(cls, data: Dict[str, dict]) -> 'NetworkData':
        """ Deserialize """
        if data is None:
            return {}

        return cls.loads(
            data,
            biomass_reaction_id=None,
            skip_orphans=False
        )

    # =========================== CLASS LOGIC ===========================

    # -- A --

    def add_simulation(self, sim: SimulationDict):
        """
        Adds a simulation

        :param sim: The simulation dictionary
        :type sim: `SimulationDict`,
        """
        id_ = sim["id"]
        self.simulations[id_] = {
            "id": id_,
            "name": sim["name"],
            "description": sim["description"]
        }

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

        self.compounds[comp.id] = comp
        self.add_compartment(comp.compartment)

        # update maps
        if comp.chebi_id:
            if comp.compartment.go_id not in self._compartment_chebi_ids:
                self._compartment_chebi_ids[comp.compartment.go_id] = {}
            self._compartment_chebi_ids[comp.compartment.go_id][comp.chebi_id] = comp.id
            # also add alternative chebi_ids
            for chebi_id in comp.alt_chebi_ids:
                self._compartment_chebi_ids[comp.compartment.go_id][chebi_id] = comp.id

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
        for substrate in rxn.substrates.values():
            comp = substrate.compound
            if not self.compound_exists(comp):
                self.add_compound(comp)

        for product in rxn.products.values():
            comp = product.compound
            if not self.compound_exists(comp):
                self.add_compound(comp)

        # add the reaction
        self.reactions[rxn.id] = rxn

        # update maps
        if rxn.rhea_id:
            self._rhea_rxn_ids_map[rxn.rhea_id] = rxn.id
        if rxn.enzyme:
            ec_number = rxn.enzyme.get("ec_number")
            if ec_number:
                self._ec_rxn_ids_map[ec_number] = rxn.id

    def add_compartment(self, compartment: Compartment):
        if not isinstance(compartment, Compartment):
            raise BadRequestException("The compartment must an instance of Compartment")
        self.compartments[compartment.id] = compartment

    # -- B --

    # -- C --

    def copy(self) -> 'NetworkData':
        from ..network import Network
        net_data: NetworkData = NetworkData()
        net_data.name = self.name
        net_data.compounds = {k: v.copy() for k, v in self.compounds.items()}
        net_data.reactions = {k: v.copy() for k, v in self.reactions.items()}
        net_data.compartments = {k: v.copy() for k, v in self.compartments.items()}
        net_data.simulations = copy.deepcopy(self.simulations)
        net_data.recon_tags = copy.deepcopy(self.recon_tags)

        net_data._compartment_chebi_ids = copy.deepcopy(self._compartment_chebi_ids)
        net_data._ec_rxn_ids_map = copy.deepcopy(self._ec_rxn_ids_map)
        net_data._rhea_rxn_ids_map = copy.deepcopy(self._rhea_rxn_ids_map)
        return net_data

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

        for rxn_id, rxn in self.reactions.items():
            for substrate in rxn.substrates.values():
                comp_id = substrate.compound.id
                stoich = substrate.stoich
                S.at[comp_id, rxn_id] -= stoich

            for product in rxn.products.values():
                comp_id = product.compound.id
                stoich = product.stoich
                S.at[comp_id, rxn_id] += stoich

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

    def dumps(self, refresh_layout: bool = False, task: Task = None) -> NetworkDict:
        """
        Dumps the network data
        """

        helper = NetworkDataDumperHelper()
        if task:
            helper.attach_task(task)
        return helper.dumps(self, refresh_layout=refresh_layout)

    # -- E --

    def compartment_exists(self, compartment: Compartment) -> bool:
        if not isinstance(compartment, Compartment):
            raise BadRequestException("The compartment must be an instance of Compartment")

        return compartment.id in self.compartments

    def compound_exists(self, comp: Compound) -> bool:
        """
        Check that a compound exists in the network

        :param rxn: The compound
        :type rxn: `gws.gena.Compound`
        :return: True if the compound exists, False otherwise
        :rtype: `bool`
        """

        if not isinstance(comp, Compound):
            raise BadRequestException("The compound must be an instance of Compound")

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

        return SlugifyHelper.slugify_id(self.name + self.DELIMITER + rxn.id)

    def flatten_compound_id(self, comp: Compound) -> str:
        """ Flatten the id of a compound """
        if not isinstance(comp, Compound):
            raise BadRequestException("The compound must be an instance of Compound")
        if not self.compound_exists(comp):
            raise BadRequestException(f"The reaction {comp.id} does not exist in the network")

        if not comp.compartment.is_extracellular():
            return SlugifyHelper.slugify_id(self.name + self.DELIMITER + comp.id)
        else:
            return comp.id

    def flatten_compartment_id(self, compartment: Compartment) -> str:
        """
        Flattens a compartment id

        :param compart_go_id: The id
        :type compart_go_id: `str`
        :param net_name: The name of the (metabolic, biological, network) context
        :type net_name: `str`
        :return: The flattened id
        :rtype: `str`
        """

        if not isinstance(compartment, Compartment):
            raise BadRequestException("The compartment must be an instance of Compartment")
        if not self.compartment_exists(compartment):
            raise BadRequestException(f"The compartment {compartment.id} does not exist in the network")

        if not compartment.is_extracellular():
            return SlugifyHelper.slugify_id(self.name + self.DELIMITER + compartment.id)
        else:
            return compartment.id

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

        return self.recon_tags["compounds"]

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
            return self.recon_tags.get(rxn_id, {}).get(tag_name)
        else:
            return self.recon_tags.get(rxn_id, {})

    def get_compound_by_id(self, comp_id: str) -> Compound:
        """
        Get a compound by its id.

        :param comp_id: The compound id
        :type comp_id: `str`
        :return: The compound or `None` if the compond is not found
        :rtype: `gena.network.Compound` or `None`
        """

        return self.compounds[comp_id]

    def get_compounds_by_chebi_id(self, chebi_id: str, compartment_go_id: Optional[str] = None) -> List[Compound]:
        """
        Get a compound by its chebi id and compartment.

        :param chebi_id: The chebi id of the compound
        :type chebi_id: `str`
        :param compartment_go_id: The go_id of the compartment
        :type compartment_go_id: `str`
        :return: The compound or `None` if the compond is not found
        :rtype: `gena.network.Compound` or `None`
        """

        if isinstance(chebi_id, float) or isinstance(chebi_id, int):
            chebi_id = f"CHEBI:{chebi_id}"

        if "CHEBI" not in chebi_id:
            chebi_id = f"CHEBI:{chebi_id}"

        if compartment_go_id:
            if compartment_go_id not in self._compartment_chebi_ids:
                return []
            c_id = self._compartment_chebi_ids[compartment_go_id].get(chebi_id)
            if c_id:
                return [self.compounds[c_id]]
            else:
                return []
        else:
            comps = []
            for d in self._compartment_chebi_ids.values():
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

        return self.reactions[rxn_id]

    def get_reaction_by_ec_number(self, ec_number: str) -> Reaction:
        """
        Get a reaction by its ec number.

        :param ec_number: The ec number of the reaction
        :type ec_number: `str`
        :return: The reaction or `None` if the reaction is not found
        :rtype: `gena.network.Reaction` or `None`
        """

        r_id = self._ec_rxn_ids_map.get(ec_number)
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

        r_id = self._rhea_rxn_ids_map.get(rhea_id)
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
                return comp
        return None

    def get_compounds_by_compartments(self, compartment_go_ids: List[str] = None) -> Dict[str, Compound]:
        """
        Get the compounds in a compartments

        :returns: The list of compounds
        :rtype: List[`gena.network.Compound`]
        """

        comps = {}
        for comp_id, comp in self.compounds.items():
            if comp.compartment.go_id in compartment_go_ids:
                comps[comp_id] = comp
        return comps

    def get_steady_compounds(self, ignore_cofactors=False) -> Dict[str, Compound]:
        """
        Get the steady compounds

        :returns: The list of steady compounds
        :rtype: List[`gena.network.Compound`]
        """

        comps = {}
        for comp_id, comp in self.compounds.items():
            if comp.is_steady():
                if ignore_cofactors and comp.is_cofactor():
                    continue
                else:
                    comps[comp_id] = comp
        return comps

    def get_non_steady_compounds(self, ignore_cofactors=False) -> Dict[str, Compound]:
        """
        Get the non-steady compounds

        :returns: The list of non-steady compounds
        :rtype: List[`gena.network.Compound`]
        """

        comps = {}
        for comp_id, comp in self.compounds.items():
            if not comp.is_steady():
                if ignore_cofactors and comp.is_cofactor():
                    continue
                else:
                    comps[comp_id] = comp
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
        for rxn_id, rxn in self.reactions.items():
            bounds.loc[rxn_id, :] = [rxn.lower_bound, rxn.upper_bound]
        return bounds

    def get_number_of_reactions(self) -> int:
        """ Get number of reactions """

        return len(self.reactions)

    def get_number_of_compounds(self) -> int:
        """ Get number of compounds """

        return len(self.compounds)

    def get_summary(self) -> dict:
        """ Return the summary of the network """
        from ...sanitizer.gap.helper.gap_finder_helper import GapFinderHelper
        biomass_rxn = self.get_biomass_reaction()
        helper = GapFinderHelper()
        dem = helper.find_deadend_compound_ids(self)
        urxn = {}
        for rxn_id, rxn in self.reactions.items():
            balance = rxn.compute_mass_and_charge_balance()
            if (balance["charge"] is not None and balance["charge"] > 0) or \
                    (balance["mass"] is not None and balance["mass"] > 0):
                urxn[rxn_id] = balance

        data = {
            "Name": self.name,
            "Number of metabolites": len(self.compounds),
            "Number of reactions": len(self.reactions),
            "Number of compartments": len(self.compartments),
            "List of compartments": [c for c in self.compartments.values()],
            "Quality control": {
                "Number of deadend metabolites": len(dem),
                "Number of unbalanced reactions": len(urxn),
                "List of deadend metabolites": dem,
                "List of unbalanced reactions": urxn,
            }
        }

        if biomass_rxn:
            data["Biomass reaction"] = {
                "ID": biomass_rxn.id,
                "Name": biomass_rxn.name,
                "Formula": [biomass_rxn.to_str()],
                "Data": biomass_rxn.data
            }
        else:
            data["Biomass reaction"] = {}

        return data

    def generate_stats(self) -> dict:
        """ Gather and return networks stats """
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
        for rxn in self.reactions.values():
            for comp_id in rxn.products:
                stats["compounds"][comp_id]["count"] += 1
            for comp_id in rxn.substrates:
                stats["compounds"][comp_id]["count"] += 1
        if stats["compound_count"]:
            for comp_id in self.compounds:
                stats["compounds"][comp_id]["frequency"] = stats["compounds"][comp_id]["count"] / stats["compound_count"]
        return stats

    # -- H --

    def has_sink(self) -> bool:
        for comp in self.compounds.values():
            if comp.is_sink():
                return True

    # -- I --

    # -- L --

    @ classmethod
    def loads(cls, data: NetworkDict, *,
              biomass_reaction_id: str = None, skip_orphans: bool = False, task: Task = None) -> 'NetworkData':
        """ Load JSON data and create a Network  """

        if not data.get("compartments"):
            raise BadRequestException("Invalid network dump. Compartments not found")
        if not data.get("metabolites"):
            raise BadRequestException("Invalid network dump. Metabolites not found")
        if not data.get("reactions"):
            raise BadRequestException("Invalid network dump. Reactions not found")

        helper = NetworkDataLoaderHelper()
        if task:
            helper.attach_task(task)
        return helper.loads(
            data,
            biomass_reaction_id=biomass_reaction_id,
            skip_orphans=skip_orphans
        )

    # -- N --

    # -- P --

    # -- R --

    def remove_compound(self, comp_id: str):
        """
        Remove a compound from the network

        :param comp_id: The id of the compound to remove
        :type comp_id: `str`
        """

        if not isinstance(comp_id, str):
            raise BadRequestException("The compound id must be a string")

        comp = self.compounds[comp_id]

        for rxn in self.reactions.values():
            if comp_id in rxn.products:
                rxn.remove_product(comp)
                continue
            if comp_id in rxn.substrates:
                rxn.remove_substrate(comp)

        del self.compounds[comp_id]

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
        return self.generate_stats()["compounds"]

    def get_compound_stats_as_table(self) -> Table:
        """ Get compound stats as table """
        dict_ = self.generate_stats()["compounds"]
        for comp_id in dict_.keys():
            dict_[comp_id]["chebi_id"] = self.compounds[comp_id].chebi_id

        df = DataFrame.from_dict(dict_, columns=["count", "frequency", "chebi_id"], orient="index")
        df = df.sort_values(by=['frequency'], ascending=False)

        return Table(data=df)

    def get_total_abs_flux_as_table(self) -> Table:
        """ Get the total absolute flux as table """
        total_flux = 0
        for rxn in self.reactions.values():
            flux_estimates = rxn.get_data_slot("flux_estimates")
            if flux_estimates is not None:
                total_flux += abs(flux_estimates["values"][0])
        df = DataFrame.from_dict({"0": [total_flux]}, columns=["total_abs_flux"], orient="index")
        return Table(data=df)

    def generate_stats_as_json(self) -> dict:
        """ Get stats as JSON """
        return self.generate_stats()

    # -- R --

    # -- S --

    # -- T --

    def to_str(self) -> str:
        """
        Returns a string representation of the network

        :rtype: `str`
        """

        _str = ""
        for rxn in self.reactions.values():
            _str += "\n" + rxn.to_str()
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
        for rxn in self.reactions.values():
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
            for substrate in rxn.substrates.values():
                comp = substrate.compound
                subs.append(comp.name + " (" + comp.chebi_id + ")")

            prods = []
            for product in rxn.products.values():
                comp = product.compound
                prods.append(comp.name + " (" + comp.chebi_id + ")")

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
        for k in self.recon_tags:
            t = self.recon_tags[k]
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

    # -- U --

    def update_reaction_recon_tag(self, tag_id, tag: dict):
        """ Update a reaction recon tag """
        if not isinstance(tag, dict):
            raise BadRequestException("The tag must be a dictionary")
        if not tag_id in self.recon_tags["reactions"]:
            self.recon_tags["reactions"][tag_id] = {}
        self.recon_tags["reactions"][tag_id].update(tag)

    def update_compound_recon_tag(self, tag_id, tag: dict):
        """ Update a compound recon tag """
        if not isinstance(tag, dict):
            raise BadRequestException("The tag must be a dictionary")
        if not tag_id in self.recon_tags["compounds"]:
            self.recon_tags["compounds"][tag_id] = {}
        self.recon_tags["compounds"][tag_id].update(tag)
