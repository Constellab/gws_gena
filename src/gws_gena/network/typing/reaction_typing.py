
from typing import TypedDict

from gws_biota import ReactionLayoutDict as BiotaReactionLayoutDict

from .enzyme_typing import EnzymeDict


class ReactionDict(TypedDict):
    id: str
    name: str
    direction: str
    lower_bound: float
    upper_bound: float
    rhea_id: str
    enzyme: EnzymeDict
    layout: BiotaReactionLayoutDict
    gene_reaction_rule: str
