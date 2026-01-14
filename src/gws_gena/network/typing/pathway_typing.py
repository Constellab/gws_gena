from typing import TypedDict


class PathwayDict(TypedDict):
    id: list | None
    name: list | None


class ReactionPathwayDict(TypedDict):
    brenda: PathwayDict | None
    kegg: PathwayDict | None
    metacyc: PathwayDict | None
