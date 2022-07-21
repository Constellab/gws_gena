# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      StrParam, Table, TableImporter, importer_decorator)

from .biomass_reaction_table import BiomassReactionTable

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("BiomassReactionTableImporter", human_name="Biomass reaction table importer",
                    target_type=BiomassReactionTable, supported_extensions=Table.ALLOWED_FILE_FORMATS)
class BiomassReactionTableImporter(TableImporter):
    """
    BiomassReactionTableImporter class

    Allows to import a `json` file and create a `BiomassReactionTable` resource object.
    The `BiomassReactionTable` is a stoichiometry table describing the composition of a cell (or organism) biomass.
    """

    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'entity_column':
        StrParam(
            default_value=BiomassReactionTable.DEFAULT_ENTITY_COLUMN,
            short_description="The name of the column containing the entities"),
        'chebi_column':
        StrParam(
            default_value=BiomassReactionTable.DEFAULT_CHEBI_COLUMN,
            short_description="The name of the column containing CheBI ID of the entities. Not all entities have CheBI IDs"),
        'biomass_column':
        StrParam(
            default_value=BiomassReactionTable.DEFAULT_BIOMASS_COLUMN,
            short_description="The name of the column containing the coefficients of the biomass equation")}

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

        params["index_column"] = None
        csv_table: BiomassReactionTable = await super().import_from_path(file, params, target_type)

        chebi_column = params.get_value("chebi_column", BiomassReactionTable.DEFAULT_CHEBI_COLUMN)
        biomass_column = params.get_value("biomass_column", BiomassReactionTable.DEFAULT_BIOMASS_COLUMN)
        entity_column = params.get_value("entity_column", BiomassReactionTable.DEFAULT_ENTITY_COLUMN)

        if not csv_table.column_exists(entity_column):
            raise BadRequestException(
                f"Cannot import BiomassReactionTable.  No entity column found (no column with name '{entity_column}')")
        if not csv_table.column_exists(chebi_column):
            raise BadRequestException(
                f"Cannot import BiomassReactionTable. No CheBI ID column found (no column with name '{chebi_column}')")
        if not csv_table.column_exists(biomass_column):
            raise BadRequestException(
                f"Cannot import BiomassReactionTable.  No biomass equation found (no column with name '{biomass_column}')")

        csv_table.entity_column = entity_column
        csv_table.biomass_column = biomass_column
        csv_table.chebi_column = chebi_column

        # set table index
        # csv_table.get_data().set_index(csv_table.chebi_column)

        return csv_table
