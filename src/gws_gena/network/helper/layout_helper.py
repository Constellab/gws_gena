# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_biota import CompoundLayout as BiotaCompoundLayout

# ####################################################################
#
# CompoundCluster class
#
# ####################################################################


class LayoutHelper:
    """ Layout Helper """

    @classmethod
    def create_biomass_layout(cls, is_biomass=False):
        """ Create biomass layout """
        if is_biomass:
            x = BiotaCompoundLayout.get_biomass_position()["x"]
            y = BiotaCompoundLayout.get_biomass_position()["y"]
        else:
            x = None
            y = None
        #     # - 2 * BiotaCompoundLayout.GRID_SCALE * BiotaCompoundLayout.GRID_INTERVAL
        #     x = cls.BIOMASS_CLUSTER_CENTER["x"]
        #     y = cls.BIOMASS_CLUSTER_CENTER["y"]

        return {
            "x": x,
            "y": y,
            "level": 1,
            "clusters": {
                "biomass": {
                    "x": x,
                    "y": y,
                    "level": 1,
                    "name": "biomass",
                    "parent": "biomass"
                }
            }
        }
