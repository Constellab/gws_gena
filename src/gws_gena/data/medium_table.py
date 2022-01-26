# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import StrRField, Table, TableFile, resource_decorator

# ####################################################################
#
# Medium Datatable class
#
# ####################################################################


@resource_decorator("MediumTable",
                    human_name="MediumTable",
                    short_description="Table of culture medium composition")
class MediumTable(Table):
    """
    Represents medium composition data table

    * The first column the a compound name (offical or user-defined name)
    * The next columns are:
      * chebi_id: the list chebi ids

    For example:

    ```
    -------------------------------------
    component           | chebi_id
    -------------------------------------
    2-oxoglutarate      | CEHBI:16810
    H20                 | CHEBI:15377
    -------------------------------------
    ```
    """

    DEFAULT_CHEBI_COLUMN = "chebi_id"
    DEFAULT_ENTITY_COLUMN = "entity"
    chebi_column: str = StrRField(default_value=DEFAULT_CHEBI_COLUMN)
    entity_column: str = StrRField(default_value=DEFAULT_ENTITY_COLUMN)

    # -- E --

    # -- F --

    def get_chebi_ids(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.chebi_column, rtype)

    def get_entities(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.entity_column, rtype)

    # -- I --

    # -- S --

    def select_by_row_positions(self, indexes: List[int]) -> 'MediumTable':
        table = super().select_by_row_positions(indexes)
        table.chebi_column = self.chebi_column
        table.entity_column = self.entity_column
        return table

    def select_by_column_positions(self, indexes: List[int]) -> 'MediumTable':
        table = super().select_by_column_positions(indexes)
        table.chebi_column = self.chebi_column
        table.entity_column = self.entity_column
        return table

    def select_by_row_name(self, name_regex: str) -> 'MediumTable':
        table = super().select_by_row_name(name_regex)
        table.chebi_column = self.chebi_column
        table.entity_column = self.entity_column
        return table

    def select_by_column_name(self, name_regex: str) -> 'MediumTable':
        table = super().select_by_column_name(name_regex)
        table.chebi_column = self.chebi_column
        table.entity_column = self.entity_column
        return table


@resource_decorator("MediumTableFile",
                    human_name="MediumTable file",
                    short_description="Table file of culture medium composition")
class MediumTableFile(TableFile):
    pass
