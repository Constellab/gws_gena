# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import StrRField, Table, TableFile, resource_decorator

FLUX_TABLE_DEFAULT_TARGET_COLUMN = "target"
FLUX_TABLE_DEFAULT_UPPER_BOUND_COLUMN = "upper_bound"
FLUX_TABLE_DEFAULT_LOWER_BOUND_COLUMN = "lower_bound"
FLUX_TABLE_DEFAULT_CONFIDENCE_SCORE_COLUMN = "confidence_score"


@resource_decorator("FluxTable",
                    human_name="FluxTable",
                    short_description="Table of metabolic flux measurements")
class FluxTable(Table):
    """
    Represents experimentally-measured (or user-defined) flux data table

    * The first column is the list of `reaction ids` and/or `ec numbers` [REQUIRED]. They uniquely identify each reaction of a network.
    * The next columns are:
      * target: value of flux measured experimentally (e.g. `mol/g DW/h`) [REQUIRED]
      * upper_bound: the upper bound of the flux (e.g. `mol/g DW/h`) [REQUIRED]
      * lower_bound: the lower bound of the flux (e.g. `mol/g DW/h`) [REQUIRED]
      * confidence_score: the confidence score of the flux [REQUIRED]

    For example:

    ```
    ------------------------------------------------------------------------------------
    id                      | target    | lower_bound  | lower_bound  | confidence_score
    ------------------------------------------------------------------------------------
    RHEA_62620_1_11_1_24    | 0.234     | 0            | 1000         | 1.0
    6.3.1.2                 | -1.234    | -5           | 0            | 1.0
    ------------------------------------------------------------------------------------
    ```
    """

    DEFAULT_TARGET_COLUMN = FLUX_TABLE_DEFAULT_TARGET_COLUMN
    DEFAULT_UPPER_BOUND_COLUMN = FLUX_TABLE_DEFAULT_UPPER_BOUND_COLUMN
    DEFAULT_LOWER_BOUND_COLUMN = FLUX_TABLE_DEFAULT_LOWER_BOUND_COLUMN
    DEFAULT_CONFIDENCE_SCORE_COLUMN = FLUX_TABLE_DEFAULT_CONFIDENCE_SCORE_COLUMN

    confidence_score_column: str = StrRField(default_value=FLUX_TABLE_DEFAULT_CONFIDENCE_SCORE_COLUMN)

    # -- C --

    # -- G --

    def get_targets(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.target_column_name, rtype)

    def get_upper_bounds(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.upper_bound_column_name, rtype)

    def get_lower_bounds(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.lower_bound_column_name, rtype)

    def get_confidence_scores(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.confidence_score_column, rtype)

    # -- I --

    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'FluxTable':
        table = super().select_by_row_indexes(indexes)
        table.confidence_score_column = self.confidence_score_column
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'FluxTable':
        table = super().select_by_column_indexes(indexes)
        table.confidence_score_column = self.confidence_score_column
        return table

    def select_by_row_name(self, name_regex: str) -> 'FluxTable':
        table = super().select_by_row_name(name_regex)
        table.confidence_score_column = self.confidence_score_column
        return table

    def select_by_column_name(self, name_regex: str) -> 'FluxTable':
        table = super().select_by_column_name(name_regex)
        table.confidence_score_column = self.confidence_score_column
        return table


@resource_decorator("FluxTableFile",
                    human_name="FluxTableFile",
                    short_description="Table file of metabolic flux measurements")
class FluxTableFile(TableFile):
    pass
