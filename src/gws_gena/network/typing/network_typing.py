
from typing import List, TypedDict

from .compartment_typing import CompartmentDict
from .compound_typing import CompoundDict
from .reaction_typing import ReactionDict

NetworkReconTagDict = TypedDict("NetworkReconTagDict", {
    "reactions": dict,
    "compounds": dict,
    "ec_numbers": dict
})

NetworkDict = TypedDict("NetworkDict", {
    "name": str,
    "metabolites": List[CompoundDict],
    "reactions": List[ReactionDict],
    "compartments": List[CompartmentDict],
    "recon_tags": NetworkReconTagDict
})
