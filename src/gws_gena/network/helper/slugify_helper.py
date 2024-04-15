
from gws_core import StringHelper


class SlugifyHelper:

    @staticmethod
    def slugify_id(_id):
        """ Utility function to sluggify compound ids """
        return StringHelper.slugify(_id, snakefy=True, to_lower=False)
