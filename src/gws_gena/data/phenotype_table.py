# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import StrRField, Table, resource_decorator

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
      * target: the value of the flux measured experimentally (e.g. `mol/L/h`) `[required]`
      * upper_bound: the upper bound of the flux (e.g. `mol/L/h`) `[required]`
      * lower_bound: the lower bound of the flux (e.g. `mol/L/h`) `[required]`
      * confidence_score: the confidence score of the flux `[required]`
      * ... : other optional columns

    For example:

    | id                  | target    | lower_bound  | lower_bound  | confidence_score   | chebi_id     |
    | --------------------|-----------|--------------|--------------|--------------------|--------------|
    | biomass             |           | 0            | 1000         | 1.0                | biomass      |
    | 2-oxoglutarate      |           | 0            | 1000         | 1.0                | CEHBI:16810  |
    | glutamine           | 1.23      | 0            | 2.0          | 1.0                | CHEBI:18050  |

    """

    DEFAULT_ENTITY_ID_COLUMN = "id"
    # DEFAULT_CHEBI_ID_COLUMN = "chebi_id"
    DEFAULT_TARGET_COLUMN = "target"
    DEFAULT_UPPER_BOUND_COLUMN = "upper_bound"
    DEFAULT_LOWER_BOUND_COLUMN = "lower_bound"
    DEFAULT_CONFIDENCE_SCORE_COLUMN = "confidence_score"

    entity_id_column_name: str = StrRField(default_value=DEFAULT_ENTITY_ID_COLUMN)
    # chebi_id_column_name: str = StrRField(default_value=DEFAULT_CHEBI_ID_COLUMN)
    target_column_name: str = StrRField(default_value=DEFAULT_TARGET_COLUMN)
    lower_bound_column_name: str = StrRField(default_value=DEFAULT_LOWER_BOUND_COLUMN)
    upper_bound_column_name: str = StrRField(default_value=DEFAULT_UPPER_BOUND_COLUMN)
    confidence_score_column: str = StrRField(default_value=DEFAULT_CONFIDENCE_SCORE_COLUMN)

    # -- C --

    # -- G --

    def get_entity_ids(self) -> list:
        return self.get_column_data(self.entity_id_column_name)

    # def get_chebi_ids(self) -> list:
    #     return self.get_column_data(self.chebi_id_column_name)

    def get_targets(self) -> list:
        return self.get_column_data(self.target_column_name)

    def get_upper_bounds(self) -> list:
        return self.get_column_data(self.upper_bound_column_name)

    def get_lower_bounds(self) -> list:
        return self.get_column_data(self.lower_bound_column_name)

    def get_confidence_scores(self) -> list:
        return self.get_column_data(self.confidence_score_column)

    # -- C --
