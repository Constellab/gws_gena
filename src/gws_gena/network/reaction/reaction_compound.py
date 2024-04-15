

class BaseReactionCompound:
    """ BaseReactionCompound """
    stoich: float = None
    compound: 'Compound' = None

    def __init__(self, compound, stoich):
        self.compound = compound
        self.stoich = abs(float(stoich))

    def copy(self):
        """ Deep copy """
        cls = type(self)
        return cls(self.compound.copy(), self.stoich)


class Product(BaseReactionCompound):
    """ Product """


class Substrate(BaseReactionCompound):
    """ Substrate """
