class BaseReactionCompound:
    """BaseReactionCompound"""

    from ..compound.compound import Compound

    stoich: float | None = None
    compound: Compound | None = None

    def __init__(self, compound: Compound | None, stoich: float | None):
        self.compound = compound
        self.stoich = abs(float(stoich)) if stoich is not None else None

    def copy(self):
        """Deep copy"""
        cls = type(self)
        return cls(self.compound.copy() if self.compound is not None else None, self.stoich)


class Product(BaseReactionCompound):
    """Product"""


class Substrate(BaseReactionCompound):
    """Substrate"""
