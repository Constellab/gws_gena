# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import BadRequestException, StrRField, Table, resource_decorator


@resource_decorator("BiomassReactionTable",
                    human_name="Biomass reaction table",
                    short_description="Stoichiometry table describing the biomass composition")
class BiomassReactionTable(Table):
    """
    BiomassReactionTable class

    A stoichiometry resource table describing the composition of the biomass.

    * The first column is the compound name (offical or user-defined name) `[required]`
    * The next columns are:
      * chebi_id: the chebi ids of componds of they are known (each chebi id must be prefixed by the keyword CHEBI:). `[required]`
      * biomass: the biomass reaction data (described like a stoichiometric matrix) `[required]`
      * other colums: these columns describe the reaction of the intermediate biomass constituents (described like a stoichiometric matrix) `[required]`

    For example:

    | component               | chebi_id    | biomass      | protein |
    |-------------------------|-------------|--------------|---------|
    | biomass                 |             | 1            |         |
    | protein                 |             | -0.3176      | 1       |
    | DNA                     |             | -0.0503      |         |
    | RNA                     |             | -0.0259      |         |
    | Cofactors               |             | -0.0216      |         |
    | Cell wall               |             | -0.115       |         |
    | Carbohydrates           |             | -0.2021      |         |
    | Phospholipids           |             | -0.1542      |         |
    | L-alanine zwitterion    | CHEBI:57972 |              | -0.5875 |
    | L-argininium(1+)        | CHEBI:32682 |              | -0.1040 |
    | L-asparagine zwitterion | CHEBI:58048 |              | -0.4755 |
    | L-aspartate(1-)         | CHEBI:29991 |              | -0.6109 |
    | L-cysteine zwitterion   | CHEBI:35235 |              | -0.4755 |
    """

    DEFAULT_CHEBI_COLUMN = "chebi_id"
    DEFAULT_BIOMASS_COLUMN = "biomass"
    DEFAULT_ENTITY_COLUMN = "entity"

    biomass_column: str = StrRField(default_value=DEFAULT_BIOMASS_COLUMN)
    chebi_column: str = StrRField(default_value=DEFAULT_CHEBI_COLUMN)
    entity_column: str = StrRField(default_value=DEFAULT_ENTITY_COLUMN)

    # -- E --

    # -- F --

    def get_chebi_ids(self) -> list:
        return self.get_column_data(self.chebi_column)

    def get_entities(self) -> list:
        return self.get_column_data(self.entity_column)

    # -- I --

    # -- S --

    def select_by_column_indexes(self, indexes: List[int]) -> 'BiomassReactionTable':
        table = super().select_by_column_indexes(indexes)
        if not self.biomass_column in table.column_names:
            raise BadRequestException("The biomass_column is required and must be selected")
        if not table.chebi_column in table.column_names:
            raise BadRequestException("The chebi_column is required and must be selected")
        if not table.entity_column in table.column_names:
            raise BadRequestException("The entity_column is required and must be selected")
        return table

    def select_by_column_names(self, filters: List['DataframeFilterName']) -> 'BiomassReactionTable':
        table = super().select_by_column_names(filters)
        if not self.biomass_column in table.column_names:
            raise BadRequestException("The biomass_column is required and must be selected")
        if not table.chebi_column in table.column_names:
            raise BadRequestException("The chebi_column is required and must be selected")
        if not table.entity_column in table.column_names:
            raise BadRequestException("The entity_column is required and must be selected")
        return table
