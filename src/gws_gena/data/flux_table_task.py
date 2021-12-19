# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      ListParam, StrParam, TableExporter, TableImporter,
                      exporter_decorator, importer_decorator)

from .flux_table import FluxTable, FluxTableFile

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("FluxTableImporter", source_type=FluxTableFile, target_type=FluxTable)
class FluxTableImporter(TableImporter):
    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'target_column_name':
        StrParam(
            default_value=FluxTable.DEFAULT_TARGET_COLUMN, human_name="Target column name",
            short_description="The name of the target column"),
        'lower_bound_column_name':
        StrParam(
            default_value=FluxTable.DEFAULT_LOWER_BOUND_COLUMN, human_name="Lower bound column name",
            short_description="The name of the lower-bound column"),
        'upper_bound_column_name':
        StrParam(
            default_value=FluxTable.DEFAULT_UPPER_BOUND_COLUMN, human_name="Upper bound column name",
            short_description="The name of the upper-bound column"),
        'confidence_score_column':
        StrParam(
            default_value=FluxTable.DEFAULT_CONFIDENCE_SCORE_COLUMN, human_name="Confidence score column name",
            short_description="The name of the upper-bound column")}

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[FluxTable]) -> FluxTable:
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
        csv_table = await super().import_from_path(file, params, target_type)

        target_column_name = params.get_value("target_column_name", FluxTable.DEFAULT_TARGET_COLUMN)
        upper_bound_column_name = params.get_value("upper_bound_column_name", FluxTable.DEFAULT_UPPER_BOUND_COLUMN)
        lower_bound_column_name = params.get_value("lower_bound_column_name", FluxTable.DEFAULT_LOWER_BOUND_COLUMN)
        confidence_score_column = params.get_value("confidence_score_column", FluxTable.DEFAULT_CONFIDENCE_SCORE_COLUMN)

        if not csv_table.column_exists(target_column_name):
            raise BadRequestException(
                f"Cannot import FluxTable. No target found (no column with name '{target_column_name}')")
        if not csv_table.column_exists(upper_bound_column_name):
            raise BadRequestException(
                f"Cannot import FluxTable. No upper bound found (no column with name '{upper_bound_column_name}')")
        if not csv_table.column_exists(lower_bound_column_name):
            raise BadRequestException(
                f"Cannot import FluxTable. No lower bound found (no column with name '{lower_bound_column_name}')")
        if not csv_table.column_exists(confidence_score_column):
            raise BadRequestException(
                f"Cannot import FluxTable. No confidence score found (no column with name '{confidence_score_column}')")

        csv_table.target_column_name = target_column_name
        csv_table.upper_bound_column_name = upper_bound_column_name
        csv_table.lower_bound_column_name = lower_bound_column_name
        csv_table.confidence_score_column = confidence_score_column
        return csv_table

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("FluxTableExporter", source_type=FluxTable, target_type=FluxTableFile)
class FluxTableExporter(TableExporter):
    pass
