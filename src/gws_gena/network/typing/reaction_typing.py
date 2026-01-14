from typing import TypedDict

from gws_biota import ReactionLayoutDict as BiotaReactionLayoutDict

from .enzyme_typing import EnzymeDict


class ReactionDict(TypedDict):
    id: str | None
    name: str | None
    direction: str | None
    lower_bound: float | None
    upper_bound: float | None
    rhea_id: str | None
    enzymes: list[EnzymeDict] | None
    layout: BiotaReactionLayoutDict | None
    gene_reaction_rule: str | None
    ec_numbers: list[str] | None
    # metabolites: dict[str, float] | None
