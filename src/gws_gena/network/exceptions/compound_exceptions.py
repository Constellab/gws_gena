
from gws_core import BadRequestException


class CompoundDuplicate(BadRequestException):
    """ CompoundDuplicate """


class SubstrateDuplicateException(BadRequestException):
    """ SubstrateDuplicateException """


class ProductDuplicateException(BadRequestException):
    """ ProductDuplicateException """

class CompoundNotFoundException(BadRequestException):
    """ CompoundNotFoundException """


class InvalidCompoundIdException(BadRequestException):
    """ InvalidCompoundIdException """
