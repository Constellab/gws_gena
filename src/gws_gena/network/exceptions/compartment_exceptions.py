
from gws_core import BadRequestException


class NoCompartmentFound(BadRequestException):
    """ NoCompartmentFound """

class InvalidCompartmentException(BadRequestException):
    """ InvalidCompartmentException """
