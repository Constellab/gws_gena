# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

# ####################################################################
#
# CompoundCluster class
#
# ####################################################################


class LayoutHelper:

    @classmethod
    def create_biomass_layout(cls):
        return {
            "x": None,
            "y": None,
            "level": 1,
            "clusters": {
                "biomass": {
                    "x": None,
                    "y": None,
                    "level": 1,
                    "name": "biomass",
                    "parent": "biomass"
                }
            }
        }
