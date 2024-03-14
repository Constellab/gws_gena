# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Optional


from gws_core import (ConfigParams, JSONView,
                      Resource, SerializableRField, Table, TableView, Task,
                      resource_decorator, view, TypingStyle)
from pandas import DataFrame

from .compartment.compartment import Compartment
from .compound.compound import Compound
from .network_data.network_data import NetworkData
from .reaction.reaction import Reaction
from .typing.network_typing import NetworkDict
from .typing.simulation_typing import SimulationDict
from .view.network_view import NetworkView


@resource_decorator("Network",
                    human_name="Network",
                    short_description="Metabolic network",
                    style=TypingStyle.material_icon(material_icon_name='hub', background_color='#EB984E'))
class Network(Resource):
    """
    Class that represents a network.

    A network is a collection of reconstructed metabolic pathways.
    """

    DEFAULT_NAME = "network"

    network_data: Dict = SerializableRField(NetworkData)

    def __init__(self):
        super().__init__()
        if not self.name:
            self.name = self.DEFAULT_NAME
            self.network_data = NetworkData()

    # -- A --

    def add_simulation(self, sim: SimulationDict):
        """
        Adds a simulation

        :param sim: The simulation dictionary
        :type sim: `SimulationDict`,
        """

        self.network_data.add_simulation(sim)

    def add_compound(self, comp: Compound):
        """
        Adds a compound

        :param comp: The compound to add
        :type comp: `gena.network.Compound`
        """

        self.network_data.add_compound(comp)

    def add_reaction(self, rxn: Reaction):
        """
        Adds a product

        :param rxn: The reaction to add
        :type rxn: `gena.network.Reaction`
        """

        self.network_data.add_reaction(rxn)

    # -- B --

    # -- C --

    @property
    def simulations(self) -> dict:
        """ Get the list of simulations """
        return self.network_data.simulations

    @property
    def compartments(self) -> dict:
        """ Get the list of compartments """
        return self.network_data.compartments

    @property
    def compounds(self) -> dict:
        """ Get the list of compounds """
        return self.network_data.compounds

    def copy(self) -> 'Network':
        """ Returns a deep copy """
        net = Network()
        net.name = self.name
        net.network_data = self.network_data.copy()
        return net

    def create_stoichiometric_matrix(self) -> DataFrame:
        """
        Create the full stoichiometric matrix of the network
        """

        return self.network_data.create_stoichiometric_matrix()

    def create_steady_stoichiometric_matrix(self, ignore_cofactors=False) -> DataFrame:
        """
        Create the steady stoichiometric matrix of the network

        We define by steady stoichiometric matrix, the submatrix of the stoichimetric matrix
        involving the steady compounds (e.g. intra-cellular compounds)
        """

        return self.network_data.create_steady_stoichiometric_matrix(ignore_cofactors)

    def create_non_steady_stoichiometric_matrix(self, include_biomass=True, ignore_cofactors=False) -> DataFrame:
        """
        Create the non-steady stoichiometric matrix of the network

        We define by non-steady stoichiometric matrix, the submatrix of the stoichimetric matrix
        involving the non-steady compounds (e.g. extra-cellular, biomass compounds)
        """

        return self.network_data.create_non_steady_stoichiometric_matrix(include_biomass, ignore_cofactors)

    def create_input_stoichiometric_matrix(self, include_biomass=True, ignore_cofactors=False) -> DataFrame:
        """
        Create the input stoichiometric matrix of the network

        We define by input stoichiometric matrix, the submatrix of the stoichimetric matrix
        involving the consumed compounds
        """

        return self.network_data.create_input_stoichiometric_matrix(include_biomass, ignore_cofactors)

    def create_output_stoichiometric_matrix(self, include_biomass=True, ignore_cofactors=False) -> DataFrame:
        """
        Create the output stoichiometric matrix of the network

        We define by input stoichiometric matrix, the submatrix of the stoichimetric matrix
        involving the excreted compounds
        """

        return self.network_data.create_output_stoichiometric_matrix(include_biomass, ignore_cofactors)

    # -- D --

    def dumps(self, refresh_layout: bool = False, task: Task = None) -> NetworkDict:
        """
        Dumps the network
        """

        return self.network_data.dumps(refresh_layout=refresh_layout, task=task)

    # -- E --

    def compound_exists(self, comp: Compound) -> bool:
        """
        Check that a compound exists in the network

        :param rxn: The compound
        :type rxn: `gws.gena.Compound`
        :return: True if the compound exists, False otherwise
        :rtype: `bool`
        """

        return self.network_data.compound_exists(comp)

    def reaction_exists(self, rxn: Reaction) -> bool:
        """
        Check that a reaction exists in the network

        :param rxn: The reaction
        :type rxn: `gws.gena.Reaction`
        :return: True if the reaction exists, False otherwise
        :rtype: `bool`
        """

        return self.network_data.reaction_exists(rxn)

    # -- E --

    # -- F --

    @classmethod
    def from_biota(cls, tax_id=None):
        net = Network()
        net.network_data = NetworkData.from_biota(tax_id=tax_id)
        net.name = net.network_data.name
        return net

    def flatten_reaction_id(self, rxn: Reaction) -> str:
        """ Flatten the id of a reaction """
        return self.network_data.flatten_reaction_id(rxn)

    def flatten_compound_id(self, comp: Compound) -> str:
        """ Flatten the id of a compound """
        return self.network_data.flatten_compound_id(comp)

    def flatten_compartment_id(self, compartment: Compartment) -> str:
        """ Flatten the id of a compartment """
        return self.network_data.flatten_compartment_id(compartment)

    def get_compound_ids(self) -> List[str]:
        """ Get all compound ids """
        return self.network_data.get_compound_ids()

    def get_reaction_ids(self) -> List[str]:
        """ Get all reaction ids """
        return self.network_data.get_reaction_ids()

    def get_compound_by_id(self, comp_id: str) -> Compound:
        """
        Get a compound by its id.

        :param comp_id: The compound id
        :type comp_id: `str`
        :return: The compound or `None` if the compond is not found
        :rtype: `gena.network.Compound` or `None`
        """

        return self.network_data.get_compound_by_id(comp_id)

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

        return self.network_data.get_compounds_by_chebi_id(chebi_id, compartment)

    def get_reaction_by_id(self, rxn_id: str) -> Reaction:
        """
        Get a reaction by its id.

        :param rxn_id: The reaction id
        :type rxn_id: `str`
        :return: The reaction or `None` if the reaction is not found
        :rtype: `gena.network.Reaction` or `None`
        """

        return self.network_data.get_reaction_by_id(rxn_id)

    def get_reaction_by_ec_number(self, ec_number: str) -> Reaction:
        """
        Get a reaction by its ec number.

        :param ec_number: The ec number of the reaction
        :type ec_number: `str`
        :return: The reaction or `None` if the reaction is not found
        :rtype: `gena.network.Reaction` or `None`
        """

        return self.network_data.get_reaction_by_ec_number(ec_number)

    def get_reaction_by_rhea_id(self, rhea_id: str) -> Reaction:
        """
        Get a reaction by its rhea id.

        :param rhea_id: The rhea id of the reaction
        :type rhea_id: `str`
        :return: The reaction or `None` if the reaction is not found
        :rtype: `gena.network.Reaction` or `None`
        """

        return self.network_data.get_reaction_by_rhea_id(rhea_id)

    def get_reactions_related_to_chebi_id(self, chebi_id: str) -> List[Reaction]:
        """ Get the reactions related to a compound with having a given CheBI ID """

        return self.network_data.get_reactions_related_to_chebi_id(chebi_id)

    def get_biomass_reaction(self) -> Reaction:
        """
        Get the biomass reaction if it exists

        :returns: The biomass reaction (or `None` if the biomass reaction does not exist)
        :rtype: `gena.network.Reaction` or `None`
        """

        return self.network_data.get_biomass_reaction()

    def get_biomass_compound(self) -> Compound:
        """
        Get the biomass compounds if it exists

        :returns: The biomass compounds
        :rtype: `gena.network.Compound`
        """

        return self.network_data.get_biomass_compound()

    def get_compounds_by_compartments(self, compartment_list: List[str] = None) -> Dict[str, Compound]:
        """
        Get the compounds in a compartments

        :returns: The list of compounds
        :rtype: List[`gena.network.Compound`]
        """

        return self.network_data.get_compounds_by_compartments(compartment_list)

    def get_steady_compounds(self, ignore_cofactors=False) -> Dict[str, Compound]:
        """
        Get the steady compounds

        :returns: The list of steady compounds
        :rtype: List[`gena.network.Compound`]
        """

        return self.network_data.get_steady_compounds(ignore_cofactors)

    def get_non_steady_compounds(self, ignore_cofactors=False) -> Dict[str, Compound]:
        """
        Get the non-steady compounds

        :returns: The list of non-steady compounds
        :rtype: List[`gena.network.Compound`]
        """

        return self.network_data.get_non_steady_compounds(ignore_cofactors)

    def get_reaction_bounds(self) -> DataFrame:
        """
        Get the reaction bounds `[lb, ub]`

        :return: The reaction bounds
        :rtype: `DataFrame`
        """

        return self.network_data.get_reaction_bounds()

    def get_number_of_reactions(self) -> int:
        """ Get number of reactions """

        return self.network_data.get_number_of_reactions()

    def get_number_of_compounds(self) -> int:
        """ Get number of compounds """

        return self.network_data.get_number_of_compounds()

    def get_compound_stats_as_json(self) -> dict:
        """ Get compound stats as JSON """

        return self.network_data.get_compound_stats_as_json()

    def get_compound_stats_as_table(self) -> Table:
        """ Get compound stats as table """

        return self.network_data.get_compound_stats_as_table()

    def get_total_abs_flux_as_table(self) -> Table:
        """ Get the total absolute flux as table """

        return self.network_data.get_total_abs_flux_as_table()

    def get_stats_as_json(self) -> dict:
        """ Get stats as JSON """

        return self.network_data.get_stats_as_json()

    def get_stats(self) -> dict:
        """ Gather and return networks stats """

        return self.network_data.get_stats()

    def get_summary(self) -> dict:
        """ Return the summary of the network """

        return self.network_data.get_summary()

    # -- H --

    def has_sink(self) -> bool:
        """ Return True if the network has sink reaction, False otherwise """

        return self.network_data.has_sink()

    # -- I --

    # -- L --

    @ classmethod
    def loads(cls, data: NetworkDict, *, biomass_reaction_id: str = None,
              skip_orphans: bool = False,
              replace_unknown_compartments: bool = False,
              biomass_metabolite_id_user: str = None,
              add_biomass: bool = False,
              task: Task = None) -> 'Network':
        """ Create a Network from JSON data  """

        network = cls()
        network.network_data = NetworkData.loads(
            data,
            biomass_reaction_id=biomass_reaction_id,
            skip_orphans=skip_orphans,
            replace_unknown_compartments=replace_unknown_compartments,
            biomass_metabolite_id_user=biomass_metabolite_id_user,
            add_biomass=add_biomass,
            task=task
        )
        network.name = network.network_data.name
        return network

    # -- N --

    # -- M --

    def merge(self, network: 'Network', inplace=False):
        """ Merge with another network """
        from .helper.network_merger import NetworkMergerHelper
        merger_helper = NetworkMergerHelper()
        return merger_helper.merge(destination_network=self, source_network=network, inplace=inplace)
    # -- P --

    # -- R --

    @property
    def reactions(self) -> dict:
        """ Get the list of reactions """

        return self.network_data.reactions

    def remove_compound(self, comp_id: str):
        """
        Remove a compound from the network

        :param comp_id: The id of the compound to remove
        :type comp_id: `str`
        """

        self.network_data.remove_compound(comp_id)

    def remove_reaction(self, rxn_id: str):
        """
        Remove a reaction from the network

        :param rxn_id: The id of the reaction to remove
        :type rxn_id: `str`
        """

        self.network_data.remove_reaction(rxn_id)

    # -- S --

    def set_simulations(self, simulations: Dict):
        """ Set simulations """
        self.network_data.set_simulations(simulations)

    # -- T --

    def to_str(self) -> str:
        """
        Returns a string representation of the network

        :rtype: `str`
        """

        return self.network_data.to_str()

    def to_csv(self) -> str:
        """
        Returns a CSV representation of the network

        :rtype: `str`
        """

        return self.network_data.to_csv()

    def to_table(self) -> Table:
        """
        Returns a Table representation of the network

        :rtype: `Table`
        """

        return self.network_data.to_table()

    def to_dataframe(self) -> DataFrame:
        """
        Returns a DataFrame representation of the network

        :rtype: `DataFrame`
        """

        return self.network_data.to_dataframe()

    # -- U --

    def update_ec_recon_tag(self, tag_id, tag_data: dict):
        """ Set a ec recon tag """

        self.network_data.update_ec_recon_tag(tag_id, tag_data)

    def update_reaction_recon_tag(self, tag_id, tag_data: dict):
        """ Set a reaction recon tag """

        self.network_data.update_reaction_recon_tag(tag_id, tag_data)

    def update_compound_recon_tag(self, tag_id, tag_data: dict):
        """ Set a compound recon tag """

        self.network_data.update_compound_recon_tag(tag_id, tag_data)

    # -- V --

    @view(view_type=NetworkView, default_view=True, human_name="Network")
    def view_as_network(self, _: ConfigParams) -> NetworkView:
        return NetworkView(data=self)

    @view(view_type=JSONView, human_name="Summary")
    def view_as_summary(self, _: ConfigParams) -> JSONView:
        """  View as summary """
        data = self.get_summary()
        j_view = JSONView()
        j_view.set_data(data=data)
        return j_view

    @ view(view_type=TableView, human_name="Reaction table")
    def view_as_table(self, _: ConfigParams) -> TableView:
        """ View as table """
        table = self.to_table()
        t_view = TableView(table)
        return t_view

    @ view(view_type=JSONView, human_name="JSON view")
    def view_as_json(self, params: ConfigParams) -> JSONView:
        """ View as json """
        json_view: JSONView = super().view_as_json(params)
        json_view.set_data(self.dumps())
        return json_view

    @ view(view_type=TableView, human_name="Reaction gaps")
    def view_gaps_as_table(self, _: ConfigParams) -> TableView:
        """ View gaps as table """
        from ..sanitizer.gap.helper.gap_finder_helper import GapFinderHelper
        helper = GapFinderHelper()
        data: DataFrame() = helper.find_gaps(self)
        table = Table(data)
        t_view = TableView(table)
        return t_view

    @ view(view_type=TableView, human_name="Compound distribution")
    def view_compound_stats_as_table(self, _: ConfigParams) -> TableView:
        """ View compound stats as table """
        table: Table = self.get_compound_stats_as_table()
        t_view = TableView(table)
        return t_view
