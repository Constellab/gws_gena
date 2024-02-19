# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import BadRequestException, StrRField, Table, resource_decorator


@resource_decorator("FluxTable",
                    human_name="Flux table",
                    short_description="Table of metabolic flux measurements")
class FluxTable(Table):
    """
    FluxTable class.

    A resource table of experimentally measured (or user-defined) metabolic fluxes.

    * The first column is the list of `reaction ids` and/or `ec numbers` `[required]`. They uniquely identify each reaction of a network.
    * The next columns are:
      * target: the value of the flux measured experimentally (e.g. `mol/gDW/h`) `[required]`
      * upper_bound: the upper bound of the flux (e.g. `mol/gDW/h`) `[required]`
      * lower_bound: the lower bound of the flux (e.g. `mol/gDW/h`) `[required]`
      * confidence_score: the confidence score of the flux `[required]`

    For example:

    | id                      | target    | lower_bound  | lower_bound  | confidence_score   |
    | ------------------------|-----------|--------------|--------------|--------------------|
    | RHEA_62620_1_11_1_24    | 0.234     | 0            | 1000         | 1.0                |
    | 6.3.1.2                 | -1.234    | -5           | 0            | 1.0                |
    """

    DEFAULT_REACTION_ID_COLUMN = "reaction_id"
    DEFAULT_TARGET_COLUMN = "target"
    DEFAULT_UPPER_BOUND_COLUMN = "upper_bound"
    DEFAULT_LOWER_BOUND_COLUMN = "lower_bound"
    DEFAULT_CONFIDENCE_SCORE_COLUMN = "confidence_score"

    reaction_id_column_name: str = StrRField(default_value=DEFAULT_REACTION_ID_COLUMN)
    target_column_name: str = StrRField(default_value=DEFAULT_TARGET_COLUMN)
    lower_bound_column_name: str = StrRField(default_value=DEFAULT_LOWER_BOUND_COLUMN)
    upper_bound_column_name: str = StrRField(default_value=DEFAULT_UPPER_BOUND_COLUMN)
    confidence_score_column: str = StrRField(default_value=DEFAULT_CONFIDENCE_SCORE_COLUMN)

    # -- C --

    # -- G --

    def get_reaction_ids(self) -> list:
        return self.get_column_data(self.reaction_id_column_name)

    def get_targets(self) -> list:
        return self.get_column_data(self.target_column_name)

    def get_upper_bounds(self) -> list:
        return self.get_column_data(self.upper_bound_column_name)

    def get_lower_bounds(self) -> list:
        return self.get_column_data(self.lower_bound_column_name)

    def get_confidence_scores(self) -> list:
        return self.get_column_data(self.confidence_score_column)

    # -- I --

    # -- S --

    def select_by_column_indexes(self, indexes: List[int]) -> 'FluxTable':
        table = super().select_by_column_indexes(indexes)
        if not self.confidence_score_column in table.column_names:
            raise BadRequestException("The confidence_score_column is required and must be selected")
        return table

    def select_by_column_names(self, filters: List['DataframeFilterName']) -> 'FluxTable':
        table = super().select_by_column_names(filters)
        if not self.confidence_score_column in table.column_names:
            raise BadRequestException("The confidence_score_column is required and must be selected")
        return table
