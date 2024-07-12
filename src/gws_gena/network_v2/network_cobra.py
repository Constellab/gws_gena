
from typing import Dict, List, Optional, TypedDict

import numpy as np
from cobra.core import Metabolite, Model, Reaction
from cobra.io import model_from_dict, model_to_dict
from gws_biota import Compartment as BiotaCompartment
from gws_core import (ConfigParams, DictRField, JSONView, Resource, Table,
                      TableView, TypingStyle, resource_decorator, view)
from gws_gena.network.view.network_view import NetworkView
from pandas import DataFrame


class ReactionSimulation(TypedDict):
    value: float
    lower_bound: float
    upper_bound: float


@resource_decorator("NetworkCobra",
                    human_name="Network Cobra",
                    short_description="Metabolic network",
                    style=TypingStyle.material_icon(material_icon_name='hub', background_color='#EB984E'))
class NetworkCobra(Resource):
    """
    Class that represents a network.

    A network is a collection of reconstructed metabolic pathways.
    """

    DEFAULT_NAME = "network"

    BIOMASS_GO_ID = "GO:0016049"
    REACTION_LOWER_BOUND = -1000.0
    REACTION_UPPER_BOUND = 1000.0

    network_dict = DictRField()

    _cobra_model: Model = None

    def __init__(self):
        super().__init__()
        if not self.name:
            self.name = self.DEFAULT_NAME

    def get_cobra_model(self) -> Model:
        if not self._cobra_model:
            self._cobra_model = model_from_dict(self.network_dict)

        return self._cobra_model

    def set_cobra_model(self, model: Model) -> None:
        self._cobra_model = model
        self.network_dict = model_to_dict(model)

    ############################################### METABOLITE  ###############################################

    def get_metabolites(self) -> List[Metabolite]:
        return self.get_cobra_model().metabolites

    def get_metabolite_ids(self):
        return [metabolite.id for metabolite in self.get_metabolites()]

    def has_metabolite(self, metabolite_id: str) -> bool:
        return metabolite_id in self.get_metabolite_ids()

    def get_metabolite_by_id(self, metabolite_id: str) -> Optional[Metabolite]:
        cobra_model = self.get_cobra_model()
        return cobra_model.metabolites.get_by_id(metabolite_id)

    def get_metabolite_by_id_and_check(self, metabolite_id: str) -> Metabolite :
        metabolite = self.get_metabolite_by_id(metabolite_id)
        if not metabolite:
            raise Exception(f"Metabolite {metabolite_id} not found")
        return metabolite

    def get_biomass_metabolite(self) -> Metabolite:
        """
        Get the biomass metabolite if it exists

        :returns: The biomass metabolite
        :rtype: Metabolite
        """
        for metabolite in self.get_metabolites():
            compartment_go_id = BiotaCompartment.get_by_bigg_id(metabolite.compartment).go_id
            if compartment_go_id == self.BIOMASS_GO_ID:
                return metabolite
        return None

    ############################################### REACTION ###############################################

    def get_reactions(self) -> List[Reaction]:
        return self.get_cobra_model().reactions

    def get_reaction_ids(self):
        return [reaction.id for reaction in self.get_reactions()]

    def has_reaction(self, reaction_id: str) -> bool:
        return reaction_id in self.get_reaction_ids()

    def get_reaction_bounds(self) -> DataFrame:
        """
        Get the reaction bounds `[lb, ub]`

        :return: The reaction bounds
        :rtype: `DataFrame`
        """

        bounds = DataFrame(
            index=self.get_reaction_ids(),
            columns=["lb", "ub"],
            data=np.zeros((len(self.get_reactions()), 2))
        )
        for reaction in self.get_reactions():
            bounds.loc[reaction.id, :] = [
                reaction.lower_bound, reaction.upper_bound]
        return bounds

    def get_reaction_by_id(self, reaction_id: str) -> Optional[Reaction]:
        cobra_model = self.get_cobra_model()
        return cobra_model.reactions.get_by_id(reaction_id)

    def get_reaction_by_id_and_check(self, reaction_id: str) -> Reaction:
        reaction = self.get_reaction_by_id(reaction_id)
        if not reaction:
            raise Exception(f"Reaction {reaction_id} not found")
        return reaction

    def get_biomass_reaction(self) -> Optional[Reaction]:
        """ Get the biomass reaction """
        for reaction in self.get_reactions():
            if "b" in reaction.compartments:
                return reaction

        return None

    def set_reaction_simulation_data(self, reaction_id: str,
                                     data: Dict[str, ReactionSimulation]) -> None:

        self.set_reaction_notes_value(reaction_id, "simulations", data)

    def get_reaction_simulation_data(self, reaction_id: str) -> Dict[str, ReactionSimulation]:
        return self.get_reaction_notes_value(reaction_id, "simulations")

    def set_reaction_notes_value(self, reaction_id: str,
                                 note_key: str,
                                 note_value: dict) -> None:

        reaction = self.get_reaction_by_id_and_check(reaction_id)
        if reaction.notes is None:
            reaction.notes = {}

        reaction.notes[note_key] = note_value

    def get_reaction_notes_value(self, reaction_id: str,
                                 note_key: str) -> dict:

        reaction = self.get_reaction_by_id_and_check(reaction_id)
        if reaction.notes is None:
            return {}

        return reaction.notes.get(note_key, {})

        ############################################### OTHER ###############################################

    def create_stoichiometric_matrix(self) -> DataFrame:
        """
        Create the full stoichiometric matrix of the network
        """
        reaction_ids = self.get_reaction_ids()
        metabolite_ids = self.get_metabolite_ids()
        stoich_df = DataFrame(
            index=metabolite_ids,
            columns=reaction_ids,
            data=np.zeros((len(metabolite_ids), len(reaction_ids)))
        )

        for reaction in self.get_reactions():
            for substrate in reaction.reactants:
                metabolite_id = substrate.id
                stoich = reaction.get_coefficient(substrate.id)
                stoich_df.at[metabolite_id, reaction.id] += stoich

            for product in reaction.products:
                metabolite_id = product.id
                stoich = reaction.get_coefficient(product.id)
                stoich_df.at[metabolite_id, reaction.id] += stoich

        return stoich_df

    @classmethod
    def from_cobra_json(cls, data: dict) -> 'NetworkCobra':
        network = cls()
        network.network_dict = data
        return network

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

    @view(view_type=TableView, human_name="Reaction table")
    def view_as_table(self, _: ConfigParams) -> TableView:
        """ View as table """
        table = self.to_table()
        t_view = TableView(table)
        return t_view

    @view(view_type=JSONView, human_name="JSON view")
    def view_as_json(self, params: ConfigParams) -> JSONView:
        """ View as json """
        json_view: JSONView = super().view_as_json(params)
        json_view.set_data(self.dumps())
        return json_view

    @view(view_type=TableView, human_name="Reaction gaps")
    def view_gaps_as_table(self, _: ConfigParams) -> TableView:
        """ View gaps as table """
        from ..sanitizer.gap.helper.gap_finder_helper import GapFinderHelper
        helper = GapFinderHelper()
        data: DataFrame() = helper.find_gaps(self)
        table = Table(data)
        t_view = TableView(table)
        return t_view

    @view(view_type=TableView, human_name="Compound distribution")
    def view_compound_stats_as_table(self, _: ConfigParams) -> TableView:
        """ View compound stats as table """
        table: Table = self.get_compound_stats_as_table()
        t_view = TableView(table)
        return t_view
