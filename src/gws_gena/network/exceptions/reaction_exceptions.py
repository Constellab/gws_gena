# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BadRequestException


class ReactionDuplicate(BadRequestException):
    """ ReactionDuplicate """


class ReactionNotFoundException(BadRequestException):
    """ ReactionNotFoundException """


class InvalidReactionException(BadRequestException):
    """ InvalidReactionException """
