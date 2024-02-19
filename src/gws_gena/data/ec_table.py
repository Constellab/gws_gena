# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import BadRequestException, StrRField, Table, resource_decorator


@resource_decorator("ECTable",
                    human_name="EC number table",
                    short_description="Table of EC numbers")
class ECTable(Table):
    """
    ECTable class

    A resource table of EC numbers

    * The first column is the compound name (official or user-defined name) `[required]`
    * The next columns are:
      * ec_number: the list of ec numbers `[required]`
      * other user informations [OPTIONAL]

    For example:

    | component           | ec_number |
    |---------------------|-----------|
    | PNEG_00964          | 1.4.1.2   |
    | PNEG_02355          | 4.2.1.10  |
    """

    DEFAULT_EC_COLUMN = "ec_number"
    ec_column: str = StrRField(default_value=DEFAULT_EC_COLUMN)

    # -- E --

    # -- G --

    def get_ec_numbers(self) -> list:
        return self.get_column_data(self.ec_column)

    # -- I --

    # -- S --

    def select_by_column_indexes(self, indexes: List[int]) -> 'ECTable':
        table = super().select_by_column_indexes(indexes)
        if not self.ec_column in table.column_names:
            raise BadRequestException("The ec_column is required and must be selected")
        return table

    def select_by_column_names(self, filters: List['DataframeFilterName']) -> 'ECTable':
        table = super().select_by_column_names(filters)
        if not self.ec_column in table.column_names:
            raise BadRequestException("The ec_column is required and must be selected")
        return table
