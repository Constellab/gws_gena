# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import StrRField, Table, TableFile, resource_decorator

BIOMASS_TABLE_DEFAULT_CHEBI_COLUMN = "chebi_id"
BIOMASS_TABLE_DEFAULT_BIOMASS_COLUMN = "biomass"


@resource_decorator("BiomassReactionTable",
                    human_name="BiomassReactionTable",
                    short_description="Stoichiometry table describint the biomass composition")
class BiomassReactionTable(Table):
    """
    Represents biomass data table

    * The first column is the compound name (offical or user-defined name) [REQUIRED]
    * The next columns are:
      * chebi_id: the chebi ids of componds of they are known (each chebi id must be prefixed by the keyword CHEBI:). [REQUIRED]
      * biomass: the biomass reaction data (described like a stoichiometric matrix) [REQUIRED]
      * other colums: these columns describe the reaction of the intermediate biomass constituents (described like a stoichiometric matrix) [REQUIRED]

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

    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'BiomassReactionTable':
        table = super().select_by_row_indexes(indexes)
        table.biomass_column = self.biomass_column
        table.chebi_column = self.chebi_column
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'BiomassReactionTable':
        table = super().select_by_column_indexes(indexes)
        table.biomass_column = self.biomass_column
        table.chebi_column = self.chebi_column
        return table

    def select_by_row_name(self, name_regex: str) -> 'BiomassReactionTable':
        table = super().select_by_row_name(name_regex)
        table.biomass_column = self.biomass_column
        table.chebi_column = self.chebi_column
        return table

    def select_by_column_name(self, name_regex: str) -> 'BiomassReactionTable':
        table = super().select_by_column_name(name_regex)
        table.biomass_column = self.biomass_column
        table.chebi_column = self.chebi_column
        return table


@resource_decorator("BiomassReactionTableFile",
                    human_name="BiomassReactionTableFile",
                    short_description="Stoichiometric table file describing biomass reactions")
class BiomassReactionTableFile(TableFile):
    pass
