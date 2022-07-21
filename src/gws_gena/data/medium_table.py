# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import BadRequestException, StrRField, Table, resource_decorator

# ####################################################################
#
# Medium Datatable class
#
# ####################################################################


@resource_decorator("MediumTable",
                    human_name="Medium table",
                    short_description="Table of culture medium composition")
class MediumTable(Table):
    """
    MediumTable class

    A resource table representing a culture medium composition

    * The first column the a compound name (offical or user-defined name) `[required]`
    * The next columns are:
      * chebi_id: the list chebi ids

    For example:

    | component           | chebi_id     |
    | --------------------|--------------|
    | 2-oxoglutarate      | CEHBI:16810  |
    | glutamine           | CHEBI:18050  |
    """

    DEFAULT_CHEBI_COLUMN = "chebi_id"
    DEFAULT_ENTITY_COLUMN = "entity"
    chebi_column: str = StrRField(default_value=DEFAULT_CHEBI_COLUMN)
    entity_column: str = StrRField(default_value=DEFAULT_ENTITY_COLUMN)

    # -- E --

    # -- F --

    def get_chebi_ids(self) -> list:
        return self.get_column_as_list(self.chebi_column)

    def get_entities(self) -> list:
        return self.get_column_as_list(self.entity_column)

    # -- I --

    # -- S --

    def select_by_column_positions(self, positions: List[int]) -> 'MediumTable':
        table = super().select_by_column_positions(positions)
        if not self.chebi_column in table.column_names:
            raise BadRequestException("The chebi_column is required and must be selected")
        if not self.entity_column in table.column_names:
            raise BadRequestException("The entity_column is required and must be selected")
        return table

    def select_by_column_names(self, names: List[str], filters: List['DataframeFilterName']) -> 'MediumTable':
        table = super().select_by_column_names(names, filters)
        if not self.chebi_column in table.column_names:
            raise BadRequestException("The chebi_column is required and must be selected")
        if not self.entity_column in table.column_names:
            raise BadRequestException("The entity_column is required and must be selected")
        return table
