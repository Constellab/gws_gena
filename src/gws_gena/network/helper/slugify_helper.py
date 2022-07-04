# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import StringHelper


class SlugifyHelper:

    @staticmethod
    def slugify_id(_id):
        """ Utility function to sluggify compound ids """
        return StringHelper.slugify(_id, snakefy=True, to_lower=False)
