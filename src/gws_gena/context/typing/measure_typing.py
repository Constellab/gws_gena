
from typing import TypedDict

from .variable_typing import VariableDict


class MeasureDict(TypedDict):
    id: str
    name: str
    lower_bound: list
    upper_bound: list
    target: list
    confidence_score: list
    variables: list[VariableDict]
