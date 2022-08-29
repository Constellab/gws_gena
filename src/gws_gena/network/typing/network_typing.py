# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, TypedDict

from .compartment_typing import CompartmentDict
from .compound_typing import CompoundDict
from .reaction_typing import ReactionDict

NetworkReconTagDict = TypedDict("NetworkReconTagDict", {
    "reactions": dict,
    "compounds": dict
})

NetworkDict = TypedDict("NetworkDict", {
    "name": str,
    "metabolites": List[CompoundDict],
    "reactions": List[ReactionDict],
    "compartments": List[CompartmentDict],
    "recon_tags": NetworkReconTagDict
})
