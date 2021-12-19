# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      ListParam, StrParam, StrRField, Table, TableExporter,
                      TableFile, TableImporter, export_to_path,
                      exporter_decorator, importer_decorator,
                      resource_decorator, task_decorator)

from .medium_table import MediumTable, MediumTableFile

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("MediumTableImporter", source_type=MediumTableFile, target_type=MediumTable)
class MediumTableImporter(TableImporter):
    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'chebi_column':
        StrParam(
            default_value=MediumTable.DEFAULT_CHEBI_COLUMN, human_name="CheBI column name",
            short_description="The CheBI ID column name"),
        'index_columns':
        ListParam(
            optional=True,
            short_description="Columns to use as the row names. Use None to prevent parsing row names. Only for CSV files")
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[MediumTable]) -> MediumTable:
        """
        Import from a repository

        Additional parameters

        :param file: The file to import
        :type file: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed medium table
        :rtype: MediumTable
        """

        index_columns = params.get_value("index_columns") or 0
        params["index_columns"] = index_columns
        csv_table = await super().import_from_path(file, params, target_type)

        chebi_column = params.get_value("chebi_column", MediumTable.DEFAULT_CHEBI_COLUMN)
        if not csv_table.column_exists(chebi_column):
            raise BadRequestException(
                f"Cannot import MediumTable. No chebi ids found (no column with name '{chebi_column}')")

        csv_table.chebi_column = chebi_column
        return csv_table

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("MediumTableExporter", source_type=MediumTable, target_type=MediumTableFile)
class MediumTableExporter(TableExporter):
    pass
