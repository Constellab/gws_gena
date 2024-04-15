
from typing import TypedDict

EnzymeDict = TypedDict("EnzymeDict", {
    "name": str,
    "tax": dict,
    "ec_number": str,
    "pathways": dict,
    "related_deprecated_enzyme": dict
})
