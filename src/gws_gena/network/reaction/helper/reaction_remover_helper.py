
from gws_core import Table
from ....data.entity_id_table import EntityIDTable
from ....helper.base_helper import BaseHelper
from ...network import Network
from ....data.task.transformer_ec_number_table import TransformerECNumberTable


class ReactionRemoverHelper(BaseHelper):

    def remove_list_of_reactions(
            self, network: Network, reaction_table: (Table, EntityIDTable),
            reverse_remove: bool = False) -> Network:
        """ Remove a list of reactions for a network """
        rxn_series = network.reactions.copy()

        # check all
        all_valid_ids = []
        for k, rxn in rxn_series.items():
            ec_number_tab = []
            for enzyme in rxn.enzymes:
                ec_number_tab.append(enzyme.get("ec_number"))
            all_valid_ids.extend([*ec_number_tab, rxn.id, rxn.rhea_id])

        if isinstance(reaction_table, (EntityIDTable, Table)):
            ec_number_name = TransformerECNumberTable.ec_number_name
            if isinstance(reaction_table, EntityIDTable):
                id_list: list = reaction_table.get_ids()
            elif reaction_table.column_exists(TransformerECNumberTable.ec_number_name):
                id_list: list = reaction_table.get_column_data(ec_number_name)

            valid_ids_to_remove = [x for x in id_list if x in all_valid_ids]
            invalid_ids_to_remove = [x for x in id_list if x not in all_valid_ids]

            if valid_ids_to_remove:
                for k, rxn in rxn_series.items():
                    ec_number_tab = []
                    for enzyme in rxn.enzymes:
                        ec_number_tab.append(enzyme.get("ec_number"))

                    rxn_ids = [*ec_number_tab, rxn.id, rxn.rhea_id]
                    is_in_list = False
                    for rxn_id in rxn_ids:
                        is_in_list = rxn_id in valid_ids_to_remove
                        if is_in_list:
                            break

                    if reverse_remove:
                        if not is_in_list:
                            network.remove_reaction(rxn.id)
                    elif is_in_list:
                        network.remove_reaction(rxn.id)

            if invalid_ids_to_remove:
                self.log_warning_message(
                    f"The following reactions were not found. Please check ids.\n{invalid_ids_to_remove}")

        else:
            self.log_warning_message("Invalid reaction table, use Transformer EC Number Table")
