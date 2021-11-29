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
# Biomass Datatable class
#
# ####################################################################

BIOMASS_TABLE_DEFAULT_CHEBI_COLUMN_NAME = "chebi_id"
BIOMASS_TABLE_DEFAULT_BIOMASS_COLUMN_NAME = "biomass"


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

    DEFAULT_CHEBI_COLUMN_NAME = BIOMASS_TABLE_DEFAULT_CHEBI_COLUMN_NAME
    DEFAULT_BIOMASS_COLUMN_NAME = BIOMASS_TABLE_DEFAULT_BIOMASS_COLUMN_NAME

    biomass_column_name: str = StrRField(default_value=BIOMASS_TABLE_DEFAULT_BIOMASS_COLUMN_NAME)
    chebi_column_name: str = StrRField(default_value=BIOMASS_TABLE_DEFAULT_CHEBI_COLUMN_NAME)

    # -- E --

    # -- F --

    def get_chebi_ids(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.chebi_column_name, rtype)

    # -- I --

    @classmethod
    @import_from_path(specs={
        **TableImporter.config_specs,
        'chebi_column_name': StrParam(default_value=BIOMASS_TABLE_DEFAULT_CHEBI_COLUMN_NAME, short_description="The CheBI ID column name"),
        'biomass_column_name': StrParam(default_value=BIOMASS_TABLE_DEFAULT_BIOMASS_COLUMN_NAME, short_description="The biomass equation column name"),
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

        index_columns = params.get_value("index_columns") or 0
        params["index_columns"] = index_columns
        csv_table = super().import_from_path(file, params)

        chebi_column_name = params.get_value("chebi_column_name", cls.DEFAULT_CHEBI_COLUMN_NAME)
        biomass_column_name = params.get_value("biomass_column_name", cls.DEFAULT_BIOMASS_COLUMN_NAME)
        if not csv_table.column_exists(chebi_column_name):
            raise BadRequestException(
                f"Cannot import BiomassTable. No CheBI ID column found (no column with name '{chebi_column_name}')")

        if not csv_table.column_exists(biomass_column_name):
            raise BadRequestException(
                f"Cannot import BiomassTable.  No biomass equation found (no column with name '{biomass_column_name}')")

        csv_table.biomass_column_name = biomass_column_name
        csv_table.chebi_column_name = chebi_column_name
        return csv_table

    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'BiomassTable':
        table = super().select_by_row_indexes(indexes)
        table = BiomassTable(data=table.get_data())
        table.biomass_column_name = self.biomass_column_name
        table.chebi_column_name = self.chebi_column_name
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'BiomassTable':
        table = super().select_by_column_indexes(indexes)
        table = BiomassTable(data=table.get_data())
        table.biomass_column_name = self.biomass_column_name
        table.chebi_column_name = self.chebi_column_name
        return table

    def select_by_row_name(self, name_regex: str) -> 'BiomassTable':
        table = super().select_by_row_name(name_regex)
        table = BiomassTable(data=table.get_data())
        table.biomass_column_name = self.biomass_column_name
        table.chebi_column_name = self.chebi_column_name
        return table

    def select_by_column_name(self, name_regex: str) -> 'BiomassTable':
        table = super().select_by_column_name(name_regex)
        table = BiomassTable(data=table.get_data())
        table.biomass_column_name = self.biomass_column_name
        table.chebi_column_name = self.chebi_column_name
        return table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("BiomassImporter", resource_type=BiomassTable)
class BiomassImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("BiomassExporter", resource_type=BiomassTable)
class BiomassExporter(TableExporter):
    pass
