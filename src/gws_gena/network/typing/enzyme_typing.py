
from typing import TypedDict


class EnzymeDict(TypedDict):
    name: str
    tax: dict
    ec_number: str
    pathways: dict
    related_deprecated_enzyme: dict
