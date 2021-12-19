# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      ListParam, StrParam, TableExporter, TableImporter,
                      exporter_decorator, importer_decorator)

from .biomass_reaction_table import BiomassReactionTable, BiomassReactionTableFile

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("BiomassReactionTableImporter", source_type=BiomassReactionTableFile,
                    target_type=BiomassReactionTable)
class BiomassReactionTableImporter(TableImporter):
    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'chebi_column': StrParam(default_value=BiomassReactionTable.DEFAULT_CHEBI_COLUMN, short_description="The CheBI ID column name"),
        'biomass_column': StrParam(default_value=BiomassReactionTable.DEFAULT_BIOMASS_COLUMN, short_description="The biomass equation column name"),
        'index_columns': ListParam(default_value=[0], short_description="Columns to use as the row names. Use None to prevent parsing row names. Only for CSV files"),
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[BiomassReactionTable]) -> BiomassReactionTable:
        """
        Import from a repository

        Additional parameters

        :param file: The file to import
        :type file: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed biomass table
        :rtype: BiomassReactionTable
        """

        csv_table: BiomassReactionTable = await super().import_from_path(file, params, target_type)

        chebi_column = params.get_value("chebi_column", BiomassReactionTable.DEFAULT_CHEBI_COLUMN)
        biomass_column = params.get_value("biomass_column", BiomassReactionTable.DEFAULT_BIOMASS_COLUMN)
        if not csv_table.column_exists(chebi_column):
            raise BadRequestException(
                f"Cannot import BiomassReactionTable. No CheBI ID column found (no column with name '{chebi_column}')")

        if not csv_table.column_exists(biomass_column):
            raise BadRequestException(
                f"Cannot import BiomassReactionTable.  No biomass equation found (no column with name '{biomass_column}')")

        csv_table.biomass_column = biomass_column
        csv_table.chebi_column = chebi_column
        return csv_table

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("BiomassReactionTableExporter", source_type=BiomassReactionTable,
                    target_type=BiomassReactionTableFile)
class BiomassReactionTableExporter(TableExporter):
    pass
