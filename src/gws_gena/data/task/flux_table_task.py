# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      StrParam, Table, TableImporter, importer_decorator)

from ..flux_table import FluxTable

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("FluxTableImporter", human_name="Flux table importer",
                    short_description="Metabolic flux table importer", target_type=FluxTable,
                    supported_extensions=Table.ALLOWED_FILE_FORMATS)
class FluxTableImporter(TableImporter):
    """
    FluxTableImporter class

    Allows to import a `csv` or `xls` file and create a `FluxTable` resource object.
    The `FluxTable` is a generic table of entity IDs (CheBI IDs, Rhea IDs, EC Numbers, User-defined IDs, ...).
    """

    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'reaction_id_column':
        StrParam(
            default_value=FluxTable.DEFAULT_REACTION_ID_COLUMN, human_name="Reaction ID column name",
            short_description="The name of the reaction id column"),
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

    def import_from_path(self, source: File, params: ConfigParams, target_type: Type[FluxTable]) -> FluxTable:
        """
        Import from a repository

        Additional parameters

        :param source: The file to import
        :type source: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed csv table
        :rtype: FluxTable
        """

        params["index_column"] = None
        csv_table = super().import_from_path(source, params, target_type)

        reaction_id_column = params.get_value("reaction_id_column", FluxTable.DEFAULT_REACTION_ID_COLUMN)
        target_column_name = params.get_value("target_column_name", FluxTable.DEFAULT_TARGET_COLUMN)
        upper_bound_column_name = params.get_value("upper_bound_column_name", FluxTable.DEFAULT_UPPER_BOUND_COLUMN)
        lower_bound_column_name = params.get_value("lower_bound_column_name", FluxTable.DEFAULT_LOWER_BOUND_COLUMN)
        confidence_score_column = params.get_value("confidence_score_column", FluxTable.DEFAULT_CONFIDENCE_SCORE_COLUMN)

        if not csv_table.column_exists(reaction_id_column):
            raise BadRequestException(
                f"Cannot import FluxTable. No reaction id found (no column with name '{reaction_id_column}')")
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

        csv_table.reaction_id_column = reaction_id_column
        csv_table.target_column_name = target_column_name
        csv_table.upper_bound_column_name = upper_bound_column_name
        csv_table.lower_bound_column_name = lower_bound_column_name
        csv_table.confidence_score_column = confidence_score_column
        return csv_table
