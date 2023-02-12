# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import BadRequestException, StrRField, Table, resource_decorator

# ####################################################################
#
# Medium Datatable class
#
# ####################################################################


@resource_decorator("PhenotypeTable",
                    human_name="Phenotype table",
                    short_description="Phenotype table")
class PhenotypeTable(Table):
    """
    Phenotype table

    The phenotype table is similar to the flux table but the fluxes are related to
    entities (metabolite, biomass) instead of reactions. Qualitative observations are described by
    upper and lower bound only

    * The first column is the list of `entity ids`. They uniquely identify each reaction of a network.
    * The next columns are:
      * target: the value of the flux measured experimentally (e.g. `mol/gDW/h`) `[required]`
      * upper_bound: the upper bound of the flux (e.g. `mol/gDW/h`) `[required]`
      * lower_bound: the lower bound of the flux (e.g. `mol/gDW/h`) `[required]`
      * confidence_score: the confidence score of the flux `[required]`

    For example:

    | entity              | chebi_id     | target    | lower_bound  | lower_bound  | confidence_score   |
    | --------------------|--------------|-----------|--------------|--------------|--------------------|
    | biomass             | biomass      |           | 0            | 1000         | 1.0                |
    | 2-oxoglutarate      | CEHBI:16810  |           | 0            | 1000         | 1.0                |
    | glutamine           | CHEBI:18050  | 1.23      | 0            | 2.0          | 1.0                |

    """

    DEFAULT_ENTITY_COLUMN = "entity"
    DEFAULT_CHEBI_ID_COLUMN = "chebi_id"
    DEFAULT_TARGET_COLUMN = "target"
    DEFAULT_UPPER_BOUND_COLUMN = "upper_bound"
    DEFAULT_LOWER_BOUND_COLUMN = "lower_bound"
    DEFAULT_CONFIDENCE_SCORE_COLUMN = "confidence_score"

    entity_column_name: str = StrRField(default_value=DEFAULT_ENTITY_COLUMN)
    chebi_id_column_name: str = StrRField(default_value=DEFAULT_CHEBI_ID_COLUMN)
    target_column_name: str = StrRField(default_value=DEFAULT_TARGET_COLUMN)
    lower_bound_column_name: str = StrRField(default_value=DEFAULT_LOWER_BOUND_COLUMN)
    upper_bound_column_name: str = StrRField(default_value=DEFAULT_UPPER_BOUND_COLUMN)
    confidence_score_column: str = StrRField(default_value=DEFAULT_CONFIDENCE_SCORE_COLUMN)

    # -- C --

    # -- G --

    def get_entity_names(self) -> list:
        return self.get_column_as_list(self.entity_column_name)

    def get_chebi_ids(self) -> list:
        return self.get_column_as_list(self.chebi_id_column_name)

    def get_targets(self) -> list:
        return self.get_column_as_list(self.target_column_name)

    def get_upper_bounds(self) -> list:
        return self.get_column_as_list(self.upper_bound_column_name)

    def get_lower_bounds(self) -> list:
        return self.get_column_as_list(self.lower_bound_column_name)

    def get_confidence_scores(self) -> list:
        return self.get_column_as_list(self.confidence_score_column)

    # -- C --
