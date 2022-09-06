# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from gws_core import BadRequestException, StrRField, Table, resource_decorator


@resource_decorator("KOTable", human_name="KO table",
                    short_description="A table containing the list of KO genes, proteins or reaction")
class KOTable(Table):
    """
    KOTable class

    A table containing the list of KO genes/proteins (Rhea IDs, EC Numbers ...)

    * The first column the IDs of the entities to KO (official or user-defined ID) `[required]`
    * The next columns are optional [OPTIONAL]

    For example:

    | ko_ids       |  ko_name               |
    | -------------|------------------------|
    | CHEBI:57972  |  L-alanine             |
    | CHEBI:32682  |  L-argininium(1+)      |
    | EC:1.1.1.1   |  alcohol dehydrogenase |
    | RHEA:16505   |  Chorismate lysis      |
    """

    DEFAULT_ID_COLUMN = "ko_id"
    id_column: str = StrRField(default_value=DEFAULT_ID_COLUMN)

    # -- E --

    # -- G --

    def get_ko_ids(self) -> list:
        return self.get_column_as_list(self.id_column,)

    # -- I --

    # -- S --

    def select_by_column_positions(self, positions: List[int]) -> 'KOTable':
        table = super().select_by_column_positions(positions)
        if not self.id_column in table.column_names:
            raise BadRequestException("The id_column is required and must be selected")
        return table

    def select_by_column_names(self, filters: List['DataframeFilterName']) -> 'KOTable':
        table = super().select_by_column_names(filters)
        if not self.id_column in table.column_names:
            raise BadRequestException("The id_column is required and must be selected")
        return table
