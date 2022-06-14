# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

# ####################################################################
#
# CompoundPosition class
#
# ####################################################################


class CompoundPosition:
    """ Compount position """
    x: float = None
    y: float = None
    z: float = None
    is_major: bool = False

    def copy(self) -> 'CompoundPosition':
        p = CompoundPosition()
        p.x = self.x
        p.y = self.y
        p.z = self.z
        p.is_major = self.is_major
        return p

# ####################################################################
#
# ReactionPosition class
#
# ####################################################################


class ReactionPosition:
    """ reaction position """
    x: float = None
    y: float = None
    z: float = None
    points: dict = None

    def __init__(self):
        self.x = None
        self.y = None
        self.z = None
        self.points = {}

    def copy(self) -> 'ReactionPosition':
        p = ReactionPosition()
        p.x = self.x
        p.y = self.y
        p.z = self.z
        p.points = self.points
        return p
