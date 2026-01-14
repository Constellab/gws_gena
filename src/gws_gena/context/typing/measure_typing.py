from typing import TypedDict

from .variable_typing import VariableDict


class MeasureDict(TypedDict):
    id: str | None
    name: str | None
    lower_bound: list | None
    upper_bound: list | None
    target: list | None
    confidence_score: list | None
    variables: list[VariableDict] | None
