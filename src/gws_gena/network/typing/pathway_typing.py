
from typing import TypedDict


class PathwayDict(TypedDict):
    id: list
    name: list

class ReactionPathwayDict(TypedDict):
    brenda: PathwayDict
    kegg: PathwayDict
    metacyc: PathwayDict
