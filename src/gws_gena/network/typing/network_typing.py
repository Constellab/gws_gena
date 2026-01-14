from typing import TypedDict

from .compartment_typing import CompartmentDict
from .compound_typing import CompoundDict
from .reaction_typing import ReactionDict


class NetworkReconTagDict(TypedDict):
    reactions: dict | None
    compounds: dict | None
    ec_numbers: dict | None


class SimulationDict(TypedDict):
    id: str | None
    name: str | None
    description: str | None


class NetworkDict(TypedDict):
    name: str | None
    metabolites: list[CompoundDict] | None
    reactions: list[ReactionDict] | None
    compartments: list[CompartmentDict] | None
    simulations: list[SimulationDict] | None
    recon_tags: NetworkReconTagDict | None
