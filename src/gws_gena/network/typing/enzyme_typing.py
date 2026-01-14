from typing import TypedDict


class EnzymeDict(TypedDict):
    name: str | None
    tax: dict | None
    ec_number: str | None
    pathways: dict | None
    related_deprecated_enzyme: dict | None
