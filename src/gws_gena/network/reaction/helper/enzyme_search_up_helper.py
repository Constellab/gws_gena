# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import Taxonomy as BiotaTaxonomy
from gws_core import BadRequestException

from ....helper.base_helper import BaseHelper


class EnzymeSearchUpHelper(BaseHelper):
    """ SearchUpHelper """

    @classmethod
    def search(cls, ec_number, tax_id, tax_search_method='bottom_up') -> list:
        """
        Search the ec_number at a given taxonomy level. If not found goes at higher taxonomy levels to find it
        """
        if tax_id:
            tax = BiotaTaxonomy.get_or_none(BiotaTaxonomy.tax_id == tax_id)
            if tax is None:
                raise BadRequestException(f"No taxonomy found with tax_id {tax_id}")

            query = BiotaEnzyme.select_and_follow_if_deprecated(
                ec_number=ec_number, tax_id=tax_id, fields=['id', 'ec_number'])

            if len(query) == 0:
                if tax_search_method == 'bottom_up':
                    query = cls.search_up(ec_number, tax)

            return query
        else:
            return []

    @classmethod
    def search_up(cls, ec_number, tax):
        """ Search for unique enzymes (i.e. enzyme orthologs) with ec_numbers at the higher taxonomy level """
        found_query = []
        query = BiotaEnzyme.select_and_follow_if_deprecated(ec_number=ec_number)
        tab = {}
        for e in query:
            if e.ec_number not in tab:
                tab[e.ec_number] = []
            tab[e.ec_number].append(e)
        for t in tax.ancestors:
            is_found = False
            for _, ec in enumerate(tab):
                e_group = tab[ec]
                for e in e_group:
                    if t.rank == "no rank":
                        continue
                    if getattr(e, "tax_"+t.rank, None) == t.tax_id:
                        found_query.append(e)
                        is_found = True
                        break  # -> stop at this taxonomy rank
                if is_found:
                    del tab[ec]
                    break
        # add remaining enzyme
        for e_group in tab.values():
            for e in e_group:
                found_query.append(e)
                break
        if found_query:
            query = found_query

        return query
