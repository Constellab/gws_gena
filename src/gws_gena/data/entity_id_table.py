# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from gws_core import BadRequestException, StrRField, Table, resource_decorator


@resource_decorator("EntityIDTable", human_name="Entity ID table",
                    short_description="Generic table of entity IDs (e.g. CheBI IDs, Rhea IDs, EC Numbers, User-defined IDs, ...)")
class EntityIDTable(Table):
    """
    EntityIDTable class

    A generic resource table of entity IDs (CheBI IDs, Rhea IDs, EC Numbers, User-defined IDs, ...)

    * The first column the ID of the entity (official or user-defined ID) `[required]`
    * The next columns are optional [OPTIONAL]

    For example:

    | id           |  name                  |
    | -------------|------------------------|
    | CHEBI:57972  |  L-alanine             |
    | CHEBI:32682  |  L-argininium(1+)      |
    | EC:1.1.1.1   |  alcohol dehydrogenase |
    | RHEA:16505   |  Chorismate lysis      |
    """

    DEFAULT_ID_COLUMN = "id"
    id_column: str = StrRField(default_value=DEFAULT_ID_COLUMN)

    # -- E --

    # -- G --

    def get_ids(self) -> list:
        return self.get_column_data(self.id_column,)

    # -- I --

    # -- S --

    def select_by_column_indexes(self, positions: List[int]) -> 'EntityIDTable':
        table = super().select_by_column_indexes(positions)
        if not self.id_column in table.column_names:
            raise BadRequestException("The id_column is required and must be selected")
        return table

    def select_by_column_names(self, filters: List['DataframeFilterName']) -> 'EntityIDTable':
        table = super().select_by_column_names(filters)
        if not self.id_column in table.column_names:
            raise BadRequestException("The id_column is required and must be selected")
        return table
