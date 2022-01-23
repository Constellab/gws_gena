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


@importer_decorator("MediumTableImporter", human_name="MediumTable importer", source_type=MediumTableFile,
                    target_type=MediumTable)
class MediumTableImporter(TableImporter):
    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'entity_column':
        StrParam(
            default_value=MediumTable.DEFAULT_ENTITY_COLUMN,
            short_description="The name of the column containing the entities"),
        'chebi_column':
        StrParam(
            default_value=MediumTable.DEFAULT_CHEBI_COLUMN, human_name="CheBI column name",
            short_description="The CheBI ID column name")
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

        params["index_column"] = None
        csv_table = await super().import_from_path(file, params, target_type)

        entity_column = params.get_value("entity_column", MediumTable.DEFAULT_ENTITY_COLUMN)
        chebi_column = params.get_value("chebi_column", MediumTable.DEFAULT_CHEBI_COLUMN)

        if not csv_table.column_exists(entity_column):
            raise BadRequestException(
                f"Cannot import MediumTable. No entity column found (no column with name '{entity_column}')")
        if not csv_table.column_exists(chebi_column):
            raise BadRequestException(
                f"Cannot import MediumTable. No CheBI ID column found (no column with name '{chebi_column}')")

        csv_table.entity_column = entity_column
        csv_table.chebi_column = chebi_column
        return csv_table

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("MediumTableExporter", human_name="MediumTable exporter", source_type=MediumTable,
                    target_type=MediumTableFile)
class MediumTableExporter(TableExporter):
    pass
