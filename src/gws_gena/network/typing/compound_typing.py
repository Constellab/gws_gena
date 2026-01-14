from typing import TypedDict

from gws_biota import CompoundLayoutDict as BiotaCompoundLayoutDict

from ..compartment.compartment import Compartment


class CompoundDict(TypedDict):
    id: str | None
    name: str | None
    charge: float | None
    mass: float | None
    monoisotopic_mass: float | None
    formula: str | None
    inchi: str | None
    compartment: Compartment | None
    chebi_id: str | None
    alt_chebi_ids: list | None
    kegg_id: str | None
    inchikey: str | None
    layout: BiotaCompoundLayoutDict | None
