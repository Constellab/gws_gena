
from typing import List, TypedDict

from .variable_typing import VariableDict

MeasureDict = TypedDict("MeasureDict", {
    "id": str,
    "name": str,
    "lower_bound": list,
    "upper_bound": list,
    "target": list,
    "confidence_score": list,
    "variables": List[VariableDict],
})
