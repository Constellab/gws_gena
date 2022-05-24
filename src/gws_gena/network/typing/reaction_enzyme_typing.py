# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import TypedDict

# ####################################################################
#
# EnzymeDict class
#
# ####################################################################

EnzymeDict = TypedDict("EnzymeDict", {
    "name": str,
    "tax": dict,
    "ec_number": str,
    "pathways": dict,
    "related_deprecated_enzyme": dict
})

# ####################################################################
#
# Pathway class
#
# ####################################################################

"""
    For example:
    {
        'kegg': {
            'id': 'rn00290; rn01110',
            'name': 'Valine, leucine and isoleucine biosynthesis; Biosynthesis of secondary metabolites'
        }
    }
"""
PathwayDict = TypedDict("PathwayDict", {
    "id": list,
    "name": list,
})

ReactionPathwayDict = TypedDict("ReactionPathwayDict", {
    "brenda": PathwayDict,
    "kegg": PathwayDict,
    "metacyc": PathwayDict,
})


class ReactionEnzyme:
    pass
