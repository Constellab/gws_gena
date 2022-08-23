# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from gws_core import BadRequestException

from .typing.variable_typing import VariableDict


class Variable:
    """
    Variable class

    A `Variable` represents a reaction flux (e.g. a flux carried by a metabolic reaction).
    """

    coefficient: float = None
    reference_id: str = None
    reference_type: str = None

    REACTION_REFERENCE_TYPE = "reaction"
    REFERENCE_TYPES = [REACTION_REFERENCE_TYPE]

    def __init__(self, dict_: VariableDict):
        if dict_ is None:
            dict_ = {}
        for key, val in dict_.items():
            setattr(self, key, val)

        if self.reference_type not in self.REFERENCE_TYPES:
            raise BadRequestException(f"Invalid reference type. The reference type must in {self.REFERENCE_TYPES}")

    def copy(self):
        """ Deep copy to variable """
        return Variable(self.dumps())

    def dumps(self):
        """ Dumps the variable """
        data = {
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "coefficient": self.coefficient
        }
        return data
