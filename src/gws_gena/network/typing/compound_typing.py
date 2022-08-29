# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import TypedDict

from gws_biota import CompoundLayoutDict as BiotaCompoundLayoutDict

from ..compartment.compartment import Compartment

CompoundDict = TypedDict("CompoundDict", {
    "id": str,
    "name": str,
    "charge": float,
    "mass": float,
    "monoisotopic_mass": float,
    "formula": str,
    "inchi": str,
    "compartment": Compartment,
    "chebi_id": str,
    "alt_chebi_ids": list,
    "kegg_id": str,
    "inchikey": str,
    "layout": BiotaCompoundLayoutDict
})
