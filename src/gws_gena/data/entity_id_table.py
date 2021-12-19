# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from gws_core import StrRField, Table, TableFile, resource_decorator

ID_TABLE_DEFAULT_NAME = "name"
ID_TABLE_DEFAULT_ID_COLUMN = "id"


@resource_decorator("EntityIDTable",
                    human_name="EntityIDTable",
                    short_description="Generic table of entity IDs (e.g. CheBI, Rhea IDs, ...)")
class EntityIDTable(Table):
    """
    Generic table of entity IDs (e.g. CheBI, Rhea IDs, ...)

    * The first column the a compound name (official or user-defined name) [REQUIRED]
    * The next columns are optional [OPTIONAL]

    For example:

    ```
    ---------------------------------
    id           |  name
    ---------------------------------
    CHEBI:57972  |  L-alanine
    CHEBI:32682  |  L-argininium(1+)
    ---------------------------------
    ```
    """

    DEFAULT_ID_COLUMN = ID_TABLE_DEFAULT_ID_COLUMN
    DEFAULT_NAME_COLUMN = ID_TABLE_DEFAULT_NAME
    id_column: str = StrRField(default_value=ID_TABLE_DEFAULT_ID_COLUMN)

    # -- E --

    # -- G --

    def get_ids(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.id_column, rtype)

    # -- I --

    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'EntityIDTable':
        table = super().select_by_row_indexes(indexes)
        table.id_column = self.id_column
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'EntityIDTable':
        table = super().select_by_column_indexes(indexes)
        table.id_column = self.id_column
        return table

    def select_by_row_name(self, name_regex: str) -> 'EntityIDTable':
        table = super().select_by_row_name(name_regex)
        table.id_column = self.id_column
        return table

    def select_by_column_name(self, name_regex: str) -> 'EntityIDTable':
        table = super().select_by_column_name(name_regex)
        table.id_column = self.id_column
        return table


@resource_decorator("EntityIDTableFile",
                    human_name="EntityIDTableFile",
                    short_description="Generic table file of entity IDs (e.g. CheBI, Rhea IDs, ...)")
class EntityIDTableFile(TableFile):
    pass
