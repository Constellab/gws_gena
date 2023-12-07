# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

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
