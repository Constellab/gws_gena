# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from gws_core import StrRField, Table, TableFile, resource_decorator


@resource_decorator("EntityIDTable", human_name="EntityIDTable",
                    short_description="Generic table of entity IDs (e.g. CheBI IDs, Rhea IDs, EC Numbers, reaction IDs, ...)")
class EntityIDTable(Table):
    """
    Generic table of entity IDs (e.g. CheBI, Rhea IDs, reaction ID, EC Numbers...)

    * The first column the ID of the entity (official or user-defined ID) [REQUIRED]
    * The next columns are optional [OPTIONAL]

    For example:

    ```
    -------------------------------------
    id           |  name
    -------------------------------------
    CHEBI:57972  |  L-alanine
    CHEBI:32682  |  L-argininium(1+)
    EC:1.1.1.1   |  alcohol dehydrogenase
    RHEA:16505   |  Chorismate lysis
    -------------------------------------
    ```
    """

    DEFAULT_ID_COLUMN = "id"
    id_column: str = StrRField(default_value=DEFAULT_ID_COLUMN)

    # -- E --

    # -- G --

    def get_ids(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.id_column, rtype)

    # -- I --

    # -- S --

    def select_by_row_positions(self, indexes: List[int]) -> 'EntityIDTable':
        table = super().select_by_row_positions(indexes)
        table.id_column = self.id_column
        return table

    def select_by_column_positions(self, indexes: List[int]) -> 'EntityIDTable':
        table = super().select_by_column_positions(indexes)
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
