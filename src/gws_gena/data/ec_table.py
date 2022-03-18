# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import BadRequestException, StrRField, Table, resource_decorator


@resource_decorator("ECTable",
                    human_name="EC number table",
                    short_description="CSV table of EC numbers")
class ECTable(Table):
    """
    Represents an ec number data table

    * The first column is the compound name (official or user-defined name) [REQUIRED]
    * The next columns are:
      * ec_number: the list of ec numbers [REQUIRED]
      * other user informations [OPTIONAL]

    For example:

    ```
    -------------------------------------
    component           | ec_number
    -------------------------------------
    PNEG_00964          | 1.4.1.2
    PNEG_02355          | 4.2.1.10
    -------------------------------------
    ```
    """

    DEFAULT_EC_COLUMN = "ec_number"
    ec_column: str = StrRField(default_value=DEFAULT_EC_COLUMN)

    # -- E --

    # -- G --

    def get_ec_numbers(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.ec_column, rtype)

    # -- I --

    # -- S --

    def select_by_row_positions(self, positions: List[int]) -> 'ECTable':
        table = super().select_by_row_positions(positions)
        table.ec_column = self.ec_column
        return table

    def select_by_column_positions(self, positions: List[int]) -> 'ECTable':
        table = super().select_by_column_positions(positions)
        if not self.ec_column in table.ec_column:
            raise BadRequestException("The ec_column is required and must be selected")
        table.ec_column = self.ec_column
        return table

    def select_by_row_names(self, names: List[str], use_regex=False) -> 'ECTable':
        table = super().select_by_row_names(names, use_regex)
        table.ec_column = self.ec_column
        return table

    def select_by_column_names(self, names: List[str], use_regex=False) -> 'ECTable':
        table = super().select_by_column_names(names, use_regex)
        if not self.ec_column in table.ec_column:
            raise BadRequestException("The ec_column is required and must be selected")
        table.ec_column = self.ec_column
        return table
