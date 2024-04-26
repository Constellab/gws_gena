
from gws_core import BadRequestException, Table

from ....data.entity_id_table import EntityIDTable
from ....helper.base_helper import BaseHelper
from ...network import Network, Reaction
from ....data.task.transformer_ec_number_table import TransformerECNumberTable

class ReactionAdderHelper(BaseHelper):
    """ ReactionAdderHelper """

    def add_reactions(self, network: Network, reaction_table: (Table, EntityIDTable),
                      tax_id: str, tax_search_method: str = 'bottom_up') -> Network:

        ec_number_name = TransformerECNumberTable.ec_number_name
        if reaction_table.column_exists(TransformerECNumberTable.ec_number_name):
            ec_list: list = reaction_table.get_column_data(ec_number_name)
            for ec in ec_list:
                try:
                    rxns = Reaction.from_biota(ec_number=ec, tax_id=tax_id,
                                               tax_search_method=tax_search_method)
                    for rxn in rxns:
                        network.add_reaction(rxn)
                except BadRequestException as err:
                    self.log_warning_message(f"A warning occured when adding reactions: {err}")

        elif isinstance(reaction_table, EntityIDTable):
            id_list: list = reaction_table.get_ids()
            for rxn_id in id_list:
                try:
                    rxns = Reaction.from_biota(rhea_id=rxn_id)
                    for rxn in rxns:
                        network.add_reaction(rxn)
                except BadRequestException as err:
                    self.log_warning_message(f"A warning occured when adding reactions: {err}")

        else:
            raise Exception(f"Cannot import reaction table : no column with name '{ec_number_name}' found or EntityIDTable, use the Transformer EC Number Table")
