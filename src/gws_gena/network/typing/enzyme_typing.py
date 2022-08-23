# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import TypedDict

EnzymeDict = TypedDict("EnzymeDict", {
    "name": str,
    "tax": dict,
    "ec_number": str,
    "pathways": dict,
    "related_deprecated_enzyme": dict
})
