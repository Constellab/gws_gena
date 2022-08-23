# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import TypedDict


PathwayDict = TypedDict("PathwayDict", {
    "id": list,
    "name": list,
})

ReactionPathwayDict = TypedDict("ReactionPathwayDict", {
    "brenda": PathwayDict,
    "kegg": PathwayDict,
    "metacyc": PathwayDict,
})
