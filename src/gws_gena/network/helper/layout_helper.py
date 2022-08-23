# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_biota import CompoundLayout as BiotaCompoundLayout

from ...helper.base_helper import BaseHelper


class LayoutHelper(BaseHelper):
    """ Layout Helper """

    def create_biomass_layout(self, is_biomass=False):
        """ Create biomass layout """
        if is_biomass:
            x = BiotaCompoundLayout.get_biomass_position()["x"]
            y = BiotaCompoundLayout.get_biomass_position()["y"]
        else:
            x = None
            y = None

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
