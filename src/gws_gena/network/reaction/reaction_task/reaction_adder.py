
from gws_core import (
    ConfigParams,
    ConfigSpecs,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    StrParam,
    Table,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingStyle,
    task_decorator,
)

from ...network import Network
from ..helper.reaction_adder_helper import ReactionAdderHelper


@task_decorator("ReactionAdder", human_name="Reaction adder", short_description="Add a list of reactions to a network",
                style=TypingStyle.material_icon(material_icon_name="sync_alt", background_color="#d9d9d9"))
class ReactionAdder(Task):
    """
    ReactionAdder class.

    Add a list of reactions to an existing network
    """

    input_specs = InputSpecs({
        'network': InputSpec(Network, human_name="Network", short_description="Network to complete"),
        'reaction_table': InputSpec(Table, human_name="Table of EC numbers or IDs", short_description="The table of reactions to add"),
    })
    output_specs = OutputSpecs({
        'network': OutputSpec(Network, human_name="Network", short_description="The network after completion"),
    })

    config_specs = ConfigSpecs({
        'tax_id': StrParam(
            default_value='', human_name="Taxonomy ID", short_description="The NCBI taxonomy id"),
        'tax_search_method':
        StrParam(
            default_value='bottom_up', human_name="Taxonomy search method",
            short_description="If 'bottom_up', the algorithm will to traverse the taxonomy tree to search in the higher taxonomy levels until a reaction is found. If 'none', the algorithm will only search at the given taxonomy level given by `tax_id`")
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        network: Network = inputs["network"]
        tax_id = params['tax_id']
        tax_search_method = params['tax_search_method']
        reaction_table = inputs["reaction_table"]

        helper = ReactionAdderHelper()
        helper.attach_message_dispatcher(self.message_dispatcher)
        helper.add_reactions(network, reaction_table, tax_id,
                             tax_search_method=tax_search_method)

        return {"network": network}
