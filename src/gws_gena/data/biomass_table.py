# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import (BadRequestException, ConfigParams, File, ListParam,
                      StrParam, StrRField, Table, TableExporter, TableImporter,
                      export_to_path, exporter_decorator, import_from_path,
                      importer_decorator, resource_decorator, task_decorator)

# ####################################################################
#
# Biomass Datatable class
#
# ####################################################################

BIOMASS_TABLE_DEFAULT_CHEBI_COLUMN = "chebi_id"
BIOMASS_TABLE_DEFAULT_BIOMASS_COLUMN = "biomass"


@resource_decorator("BiomassTable",
                    human_name="BiomassTable",
                    short_description="CSV table describing biomass composition")
class BiomassTable(Table):
    """
    Represents biomass data table

    * The first column the a compound name (offical or user-defined name)
    * The next columns are:
      * chebi_id: the chebi ids of componds of they are known (each chebi id must be prefixed by the keyword CHEBI:).
      * biomass: the biomass reaction data (described like a stoichiometric matrix)
      * other colums: these columns describe the reaction of the intermediate biomass constituents (described like a stoichiometric matrix)

    For example:

    ```
    -------------------------------------------------------------------
    component               | chebi_id    | biomass      | protein
    -------------------------------------------------------------------
    biomass                 |             | 1            |
    protein                 |             | -0,317663551 | 1
    DNA                     |             | -0,050537383 |
    RNA                     |             | -0,025990654 |
    Cofactors               |             | -0,021658879 |
    Cell wall               |             | -0,115       |
    Carbohydrates           |             | -0,202149533 |
    Phospholipids           |             | -0,154266667 |
    L-alanine zwitterion    | CHEBI:57972 |              | -0,587530055
    L-argininium(1+)        | CHEBI:32682 |              | -0,104025999
    L-asparagine zwitterion | CHEBI:58048 |              | -0,47552295
    L-aspartate(1-)         | CHEBI:29991 |              | -0,610918536
    L-cysteine zwitterion   | CHEBI:35235 |              | -0,475540207
    -------------------------------------------------------------------
    ```
    """

    DEFAULT_CHEBI_COLUMN = BIOMASS_TABLE_DEFAULT_CHEBI_COLUMN
    DEFAULT_BIOMASS_COLUMN = BIOMASS_TABLE_DEFAULT_BIOMASS_COLUMN

    biomass_column: str = StrRField(default_value=BIOMASS_TABLE_DEFAULT_BIOMASS_COLUMN)
    chebi_column: str = StrRField(default_value=BIOMASS_TABLE_DEFAULT_CHEBI_COLUMN)

    # -- E --

    # -- F --

    def get_chebi_ids(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.chebi_column, rtype)

    # -- I --

    @classmethod
    @import_from_path(specs={
        **TableImporter.config_specs,
        'chebi_column': StrParam(default_value=BIOMASS_TABLE_DEFAULT_CHEBI_COLUMN, short_description="The CheBI ID column name"),
        'biomass_column': StrParam(default_value=BIOMASS_TABLE_DEFAULT_BIOMASS_COLUMN, short_description="The biomass equation column name"),
        'index_columns': ListParam(default_value=[0], short_description="Columns to use as the row names. Use None to prevent parsing row names. Only for CSV files"),
    })
    def import_from_path(cls, file: File, params: ConfigParams) -> 'BiomassTable':
        """
        Import from a repository

        Additional parameters

        :param file: The file to import
        :type file: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed biomass table
        :rtype: BiomassTable
        """

        csv_table = super().import_from_path(file, params)

        chebi_column = params.get_value("chebi_column", cls.DEFAULT_CHEBI_COLUMN)
        biomass_column = params.get_value("biomass_column", cls.DEFAULT_BIOMASS_COLUMN)
        if not csv_table.column_exists(chebi_column):
            raise BadRequestException(
                f"Cannot import BiomassTable. No CheBI ID column found (no column with name '{chebi_column}')")

        if not csv_table.column_exists(biomass_column):
            raise BadRequestException(
                f"Cannot import BiomassTable.  No biomass equation found (no column with name '{biomass_column}')")

        csv_table.biomass_column = biomass_column
        csv_table.chebi_column = chebi_column
        return csv_table

    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'BiomassTable':
        table = super().select_by_row_indexes(indexes)
        table = BiomassTable(data=table.get_data())
        table.biomass_column = self.biomass_column
        table.chebi_column = self.chebi_column
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'BiomassTable':
        table = super().select_by_column_indexes(indexes)
        table = BiomassTable(data=table.get_data())
        table.biomass_column = self.biomass_column
        table.chebi_column = self.chebi_column
        return table

    def select_by_row_name(self, name_regex: str) -> 'BiomassTable':
        table = super().select_by_row_name(name_regex)
        table = BiomassTable(data=table.get_data())
        table.biomass_column = self.biomass_column
        table.chebi_column = self.chebi_column
        return table

    def select_by_column_name(self, name_regex: str) -> 'BiomassTable':
        table = super().select_by_column_name(name_regex)
        table = BiomassTable(data=table.get_data())
        table.biomass_column = self.biomass_column
        table.chebi_column = self.chebi_column
        return table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("BiomassTableImporter", resource_type=BiomassTable)
class BiomassTableImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("BiomassTableExporter", resource_type=BiomassTable)
class BiomassTableExporter(TableExporter):
    pass
