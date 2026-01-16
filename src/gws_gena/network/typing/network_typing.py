
from typing import TypedDict

from .compartment_typing import CompartmentDict
from .compound_typing import CompoundDict
from .reaction_typing import ReactionDict


class NetworkReconTagDict(TypedDict):
    reactions: dict
    compounds: dict
    ec_numbers: dict

class NetworkDict(TypedDict):
    name: str
    metabolites: list[CompoundDict]
    reactions: list[ReactionDict]
    compartments: list[CompartmentDict]
    recon_tags: NetworkReconTagDict
