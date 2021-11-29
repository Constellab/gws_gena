# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import (BadRequestException, ConfigParams, File, StrParam,
                      StrRField, Table, TableExporter, TableImporter,
                      export_to_path, exporter_decorator, import_from_path,
                      importer_decorator, resource_decorator, task_decorator)

# ####################################################################
#
# Flux Datatable class
#
# ####################################################################

FLUX_TABLE_DEFAULT_TARGET_COLUMN_NAME = "target"
FLUX_TABLE_DEFAULT_UPPER_BOUND_COLUMN_NAME = "upper_bound"
FLUX_TABLE_DEFAULT_LOWER_BOUND_COLUMN_NAME = "lower_bound"
FLUX_TABLE_DEFAULT_CONFIDENCE_SCORE_COLUMN_NAME = "confidence_score"


@resource_decorator("FluxTable",
                    human_name="FluxTable",
                    short_description="CSV table of experimental metabolic fluxes")
class FluxTable(Table):
    """
    Represents experimentally-measured (or user-defined) flux data table

    * The first column is the list of `reaction ids` and/or `ec numbers`. They uniquely identify each reaction of a network.
    * The next columns are:
      * target: value of flux measured experimentally (e.g. `mol/g DW/h`)
      * upper_bound: the upper bound of the flux (e.g. `mol/g DW/h`)
      * lower_bound: the lower bound of the flux (e.g. `mol/g DW/h`)
      * confidence_score: the confidence score of the flux

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

    DEFAULT_TARGET_COLUMN_NAME = FLUX_TABLE_DEFAULT_TARGET_COLUMN_NAME
    DEFAULT_UPPER_BOUND_COLUMN_NAME = FLUX_TABLE_DEFAULT_UPPER_BOUND_COLUMN_NAME
    DEFAULT_LOWER_BOUND_COLUMN_NAME = FLUX_TABLE_DEFAULT_LOWER_BOUND_COLUMN_NAME
    DEFAULT_CONFIDENCE_SCORE_COLUMN_NAME = FLUX_TABLE_DEFAULT_CONFIDENCE_SCORE_COLUMN_NAME

    confidence_score_column_name: str = StrRField(default_value=FLUX_TABLE_DEFAULT_CONFIDENCE_SCORE_COLUMN_NAME)

    # -- C --

    # -- G --

    def get_targets(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.target_column_name, rtype)

    def get_upper_bounds(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.upper_bound_column_name, rtype)

    def get_lower_bounds(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.lower_bound_column_name, rtype)

    def get_confidence_scores(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.confidence_score_column_name, rtype)

    # -- I --

    @classmethod
    @import_from_path(
        specs={**TableImporter.config_specs,
               'target_column_name':
               StrParam(
                   default_value=FLUX_TABLE_DEFAULT_TARGET_COLUMN_NAME, human_name="Target column name",
                   short_description="The name of the target column"),
               'lower_bound_column_name':
               StrParam(
                   default_value=FLUX_TABLE_DEFAULT_LOWER_BOUND_COLUMN_NAME,
                   human_name="Lower bound column name",
                   short_description="The name of the lower-bound column"),
               'upper_bound_column_name':
               StrParam(
                   default_value=FLUX_TABLE_DEFAULT_UPPER_BOUND_COLUMN_NAME,
                   human_name="Upper bound column name",
                   short_description="The name of the upper-bound column"),
               'confidence_score_column_name':
               StrParam(
                   default_value=FLUX_TABLE_DEFAULT_CONFIDENCE_SCORE_COLUMN_NAME,
                   human_name="Confidence score column name",
                   short_description="The name of the upper-bound column"), })
    def import_from_path(cls, file: File, params: ConfigParams) -> 'FluxTable':
        """
        Import from a repository

        Additional parameters

        :param file: The file to import
        :type file: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed csv table
        :rtype: FluxTable
        """

        index_columns = params.get_value("index_columns") or 0
        params["index_columns"] = index_columns
        csv_table = super().import_from_path(file, params)

        target_column_name = params.get_value("target_column_name", cls.DEFAULT_TARGET_COLUMN_NAME)
        upper_bound_column_name = params.get_value("upper_bound_column_name", cls.DEFAULT_UPPER_BOUND_COLUMN_NAME)
        lower_bound_column_name = params.get_value("lower_bound_column_name", cls.DEFAULT_LOWER_BOUND_COLUMN_NAME)
        confidence_score_column_name = params.get_value(
            "confidence_score_column_name", cls.DEFAULT_CONFIDENCE_SCORE_COLUMN_NAME)

        if not csv_table.column_exists(target_column_name):
            raise BadRequestException(
                f"Cannot import FluxTable. No target found (no column with name '{target_column_name}')")
        if not csv_table.column_exists(upper_bound_column_name):
            raise BadRequestException(
                f"Cannot import FluxTable. No upper bound found (no column with name '{upper_bound_column_name}')")
        if not csv_table.column_exists(lower_bound_column_name):
            raise BadRequestException(
                f"Cannot import FluxTable. No lower bound found (no column with name '{lower_bound_column_name}')")
        if not csv_table.column_exists(confidence_score_column_name):
            raise BadRequestException(
                f"Cannot import FluxTable. No confidence score found (no column with name '{confidence_score_column_name}')")

        csv_table.target_column_name = target_column_name
        csv_table.upper_bound_column_name = upper_bound_column_name
        csv_table.lower_bound_column_name = lower_bound_column_name
        csv_table.confidence_score_column_name = confidence_score_column_name
        return csv_table

    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'FluxTable':
        table = super().select_by_row_indexes(indexes)
        table = FluxTable(data=table.get_data())
        table.confidence_score_column_name = self.confidence_score_column_name
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'FluxTable':
        table = super().select_by_column_indexes(indexes)
        table = FluxTable(data=table.get_data())
        table.confidence_score_column_name = self.confidence_score_column_name
        return table

    def select_by_row_name(self, name_regex: str) -> 'FluxTable':
        table = super().select_by_row_name(name_regex)
        table = FluxTable(data=table.get_data())
        table.confidence_score_column_name = self.confidence_score_column_name
        return table

    def select_by_column_name(self, name_regex: str) -> 'FluxTable':
        table = super().select_by_column_name(name_regex)
        table = FluxTable(data=table.get_data())
        table.confidence_score_column_name = self.confidence_score_column_name
        return table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("FluxImporter", resource_type=FluxTable)
class FluxImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("FluxExporter", resource_type=FluxTable)
class FluxExporter(TableExporter):
    pass
