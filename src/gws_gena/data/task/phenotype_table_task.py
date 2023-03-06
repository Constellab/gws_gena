# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      StrParam, Table, TableImporter, importer_decorator)

from ..phenotype_table import PhenotypeTable

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("PhenotypeTableImporter", human_name="Phenotype table importer",
                    short_description="Phenotype table importer importer", target_type=PhenotypeTable,
                    supported_extensions=Table.ALLOWED_FILE_FORMATS)
class PhenotypeTableImporter(TableImporter):
    """
    PhenotypeTableImporter class

    Allows to import a `csv` or `xls` file and create a `PhenotypeTable` resource object.
    The `PhenotypeTable` is a generic table of entity IDs (CheBI IDs, Rhea IDs, EC Numbers, User-defined IDs, ...).
    """

    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'entity_column':
        StrParam(
            default_value=PhenotypeTable.DEFAULT_ENTITY_COLUMN, human_name="Entity column name",
            short_description="The name of the column of entities"),
        'chebi_id_column':
        StrParam(
            default_value=PhenotypeTable.DEFAULT_CHEBI_ID_COLUMN, human_name="Chebi ID column name",
            short_description="The name of the chebi id column"),
        'target_column_name':
        StrParam(
            default_value=PhenotypeTable.DEFAULT_TARGET_COLUMN, human_name="Target column name",
            short_description="The name of the target column"),
        'lower_bound_column_name':
        StrParam(
            default_value=PhenotypeTable.DEFAULT_LOWER_BOUND_COLUMN, human_name="Lower bound column name",
            short_description="The name of the lower-bound column"),
        'upper_bound_column_name':
        StrParam(
            default_value=PhenotypeTable.DEFAULT_UPPER_BOUND_COLUMN, human_name="Upper bound column name",
            short_description="The name of the upper-bound column"),
        'confidence_score_column':
        StrParam(
            default_value=PhenotypeTable.DEFAULT_CONFIDENCE_SCORE_COLUMN, human_name="Confidence score column name",
            short_description="The name of the upper-bound column")}

    def import_from_path(self, source: File, params: ConfigParams, target_type: Type[PhenotypeTable]) -> PhenotypeTable:
        """
        Import from a repository

        Additional parameters

        :param source: The file to import
        :type source: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed csv table
        :rtype: PhenotypeTable
        """

        params["index_column"] = None
        csv_table = super().import_from_path(source, params, target_type)

        entity_column = params.get_value("entity_column", PhenotypeTable.DEFAULT_ENTITY_COLUMN)
        chebi_id_column = params.get_value("chebi_id_column", PhenotypeTable.DEFAULT_CHEBI_ID_COLUMN)
        target_column_name = params.get_value("target_column_name", PhenotypeTable.DEFAULT_TARGET_COLUMN)
        upper_bound_column_name = params.get_value("upper_bound_column_name", PhenotypeTable.DEFAULT_UPPER_BOUND_COLUMN)
        lower_bound_column_name = params.get_value("lower_bound_column_name", PhenotypeTable.DEFAULT_LOWER_BOUND_COLUMN)
        confidence_score_column = params.get_value(
            "confidence_score_column", PhenotypeTable.DEFAULT_CONFIDENCE_SCORE_COLUMN)

        if not csv_table.column_exists(entity_column):
            raise BadRequestException(
                f"Cannot import PhenotypeTable. No entity found (no column with name '{entity_column}')")
        if not csv_table.column_exists(chebi_id_column):
            raise BadRequestException(
                f"Cannot import PhenotypeTable. No reaction id found (no column with name '{chebi_id_column}')")
        if not csv_table.column_exists(target_column_name):
            raise BadRequestException(
                f"Cannot import PhenotypeTable. No target found (no column with name '{target_column_name}')")
        if not csv_table.column_exists(upper_bound_column_name):
            raise BadRequestException(
                f"Cannot import PhenotypeTable. No upper bound found (no column with name '{upper_bound_column_name}')")
        if not csv_table.column_exists(lower_bound_column_name):
            raise BadRequestException(
                f"Cannot import PhenotypeTable. No lower bound found (no column with name '{lower_bound_column_name}')")
        if not csv_table.column_exists(confidence_score_column):
            raise BadRequestException(
                f"Cannot import PhenotypeTable. No confidence score found (no column with name '{confidence_score_column}')")

        csv_table.entity_column = entity_column
        csv_table.chebi_id_column = chebi_id_column
        csv_table.target_column_name = target_column_name
        csv_table.upper_bound_column_name = upper_bound_column_name
        csv_table.lower_bound_column_name = lower_bound_column_name
        csv_table.confidence_score_column = confidence_score_column
        return csv_table
