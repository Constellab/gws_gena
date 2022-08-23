# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import TypedDict

from gws_biota import ReactionLayoutDict as BiotaReactionLayoutDict

from .enzyme_typing import EnzymeDict

ReactionDict = TypedDict("ReactionDict", {
    "id": str,
    "name": str,
    "direction": str,
    "lower_bound": float,
    "upper_bound": float,
    "rhea_id": str,
    "enzyme": EnzymeDict,
    "layout": BiotaReactionLayoutDict,
})
