
from gws_core import BadRequestException


class ReactionDuplicate(BadRequestException):
    """ ReactionDuplicate """


class ReactionNotFoundException(BadRequestException):
    """ ReactionNotFoundException """


class InvalidReactionException(BadRequestException):
    """ InvalidReactionException """
