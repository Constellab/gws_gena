
from typing import List, Tuple
from gws_core import Table

from ....helper.base_helper import BaseHelper
from ...network import Network
from ....data.task.transformer_ec_number_table import TransformerECNumberTable
from ....data.task.transformer_entity_id_table import TransformerEntityIDTable


class ReactionKnockOutHelper(BaseHelper):
    """ ReactionKnockOutHelper """

    FLUX_EPSILON = 1e-9

    def knockout_list_of_reactions(
            self, network: Network, reaction_table: Table,
            ko_delimiter=None, inplace=False) -> Tuple[Network, List]:
        """ knockout a list of reactions in a network """

        if inplace:
            new_net = network
        else:
            new_net: Network = network.copy()

        all_ids = []
        found_id = []

        id_column_name = TransformerEntityIDTable.id_column
        ec_number_name = TransformerECNumberTable.ec_number_name

        if isinstance(reaction_table, Table) and (reaction_table.column_exists(id_column_name) or reaction_table.column_exists(ec_number_name)) :
            # ko using RXN_ID and EC_NUMBER
            if reaction_table.column_exists(id_column_name):
                name_column_ids = id_column_name
            elif reaction_table.column_exists(ec_number_name):
                name_column_ids = ec_number_name

            id_list: list = reaction_table.get_column_data(name_column_ids)

            for rxn_id, rxn in new_net.reactions.items():
                rhea_id = rxn.rhea_id
                ec_number_tab = []
                for enzyme in rxn.enzymes:
                    ec_number_tab.append(enzyme.get("ec_number"))

                for _, ko_id_str in enumerate(id_list):
                    if ko_delimiter:
                        ko_ids = ko_id_str.split(ko_delimiter)
                    else:
                        ko_ids = [ko_id_str]
                    all_ids.extend(ko_ids)

                    for ko_id in ko_ids:
                        if ko_id in [rxn_id, rhea_id, *ec_number_tab]:
                            rxn.lower_bound = -self.FLUX_EPSILON
                            rxn.upper_bound = self.FLUX_EPSILON
                            found_id.append(ko_id)
        else:
            raise Exception(f"Cannot import KO Table: no column with name '{ec_number_name}' or '{id_column_name}' found, use the Transformer EC Number Table or Transformer Entity id Table")

        # write warnings
        not_found_id = []
        all_ids = list(set(all_ids))
        for ko_id in all_ids:
            if ko_id not in found_id:
                not_found_id.append(ko_id)
                message = f"The KO ID '{ko_id}' is not found. Please check the KO table."
                self.log_warning_message(message)
        return new_net, not_found_id
