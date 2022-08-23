# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

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
