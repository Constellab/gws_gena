
from .typing.variable_typing import VariableDict


class Variable:
    """
    Variable class

    Represents a reaction flux (for instance, a flux carried by a metabolic reaction).
    """

    coefficient: float | None = None
    reference_id: str | None = None

    def __init__(self, dict_: VariableDict):
        if dict_ is None:
            dict_ = {}
        for key, val in dict_.items():
            setattr(self, key, val)

    def copy(self):
        """ Deep copy to variable """
        return Variable(self.dumps())

    def dumps(self) -> VariableDict:
        """ Dumps the variable """
        data = VariableDict(
            reference_id=self.reference_id or "",
            coefficient=self.coefficient or 0.0
        )
        return data
