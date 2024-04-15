
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
