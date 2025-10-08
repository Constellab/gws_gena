
from gws_core import (BadRequestException, ConfigParams, InputSpec, InputSpecs,
                      OutputSpec, OutputSpecs, StringHelper, StrParam, Table,
                      Task, TaskInputs, TaskOutputs, TypingStyle, ConfigSpecs,
                      task_decorator)

from ..data.task.transformer_biomass_reaction_table import \
    TransformerBiomassReactionTable
from ..data.task.transformer_ec_number_table import TransformerECNumberTable
from ..network.network import Network
from .helper.recon_helper import ReconHelper


@task_decorator("DraftRecon001", human_name="Draft recon", short_description="Draft network reconstruction",
                style=TypingStyle.material_icon(material_icon_name="build", background_color="#d9d9d9"))
class DraftRecon(Task):
    """
    DraftRecon task.

    This task performs a draft reconstruction of a metabolic network using a list of EC numbers or taxonomy IDs.

    In input, you need to provide at least a resource EC number Table or set the parameter "tax_id".
    You can also add a Biomass Reaction Table describing the composition of a cell (or organism) biomass.

    """

    input_specs = InputSpecs({
        'ec_table': InputSpec(Table, human_name="Table of ec numbers", optional=True),
        'biomass_table': InputSpec(Table, optional=True),
    })
    output_specs = OutputSpecs({'network': OutputSpec(Network)})
    config_specs = ConfigSpecs({
        'unique_name': StrParam(
            default_value=StringHelper.generate_random_chars(4), human_name="Network name", short_description="The unique name of the network. Required to uniquely identify taxa in microbial communities"),
        'tax_id': StrParam(
            default_value='', human_name="Taxonomy ID", short_description="The NCBI taxonomy id. For example: `tax_id = 562` for E. Coli"),
        'tax_search_method':
        StrParam(
            default_value='bottom_up', allowed_values=['none', 'bottom_up'], human_name="Taxonomy search method",
            short_description="If 'bottom_up', the algorithm will to traverse the taxonomy tree to search at higher taxonomy levels until a reaction is found. If `none`, the algorithm will only search at the given taxonomy level given by `tax_id`")})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = self._create_network(params, inputs)
        helper = ReconHelper()
        helper.attach_message_dispatcher(self.message_dispatcher)

        if inputs.get('biomass_table'):
            biomass_table = inputs['biomass_table']
            biomass_column_name = TransformerBiomassReactionTable.biomass_column_name
            if not biomass_table.column_exists(biomass_column_name):
                raise Exception(
                    f"Cannot import Biomass Table: no column with name '{biomass_column_name}' use the Transformer Biomass Reaction Table")

            helper.add_biomass_equation_to_network(net, biomass_table)

        return {"network": net}

    def _create_network(self, params, inputs):
        helper = ReconHelper()
        helper.attach_message_dispatcher(self.message_dispatcher)
        unique_name = params["unique_name"]
        tax_id = params['tax_id']
        tax_search_method = params['tax_search_method']
        if not tax_search_method:
            tax_search_method = None
        if inputs.get('ec_table'):
            ec_number_name = TransformerECNumberTable.ec_number_name
            if not inputs['ec_table'].column_exists(ec_number_name):
                raise Exception(
                    f"Cannot import EC Table: no column with name '{ec_number_name}' use the Transformer EC Number Table")
            return helper.create_network_with_ec_table(
                unique_name=unique_name,
                ec_table=inputs['ec_table'],
                tax_id=params['tax_id'],
                tax_search_method=tax_search_method
            )
        elif tax_id:
            return helper.create_network_with_taxonomy(
                unique_name=unique_name,
                tax_id=params['tax_id'],
                tax_search_method=tax_search_method
            )
        else:
            raise BadRequestException(
                "A list of ec_numbers or a taxonomy_id is required")
