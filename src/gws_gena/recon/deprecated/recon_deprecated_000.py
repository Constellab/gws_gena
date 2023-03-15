# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BadRequestException, ConfigParams, InputSpec, OutputSpec,
                      StringHelper, StrParam, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ...data.biomass_reaction_table import BiomassReactionTable
from ...data.ec_table import ECTable
from ...data.medium_table import MediumTable
from ...network.network import Network
from ..helper.recon_helper import ReconHelper


@task_decorator("DraftRecon", human_name="Draft recon", short_description="Draft network reconstruction",
                deprecated_since="0.5.0", deprecated_message="Please reconsider to user the laters version of DraftRecon")
class DraftRecon000(Task):
    """
    DraftRecon task.

    This task performs a draft reconstruction of a metabolic network using a list of EC numbers or taxonomy IDs.
    """

    input_specs = {
        'ec_table': InputSpec(ECTable, human_name="Table of EC numbers", is_optional=True),
        'biomass_table': InputSpec(BiomassReactionTable, is_optional=True),
        'medium_table': InputSpec(MediumTable, is_optional=True)
    }
    output_specs = {'network': OutputSpec(Network)}
    config_specs = {
        'unique_name': StrParam(
            default_value=StringHelper.generate_random_chars(4), human_name="Network name", short_description="The unique name of the network. Required to uniquely identify taxa in microbial communities"),
        'tax_id': StrParam(
            default_value='', human_name="Taxonomy ID", short_description="The NCBI taxonomy id. For example: `tax_id = 562` for E. Coli"),
        'tax_search_method':
        StrParam(
            default_value='bottom_up', allowed_values=['none', 'bottom_up'], human_name="Taxonomy search method",
            short_description="If 'bottom_up', the algorithm will to traverse the taxonomy tree to search at higher taxonomy levels until a reaction is found. If `none`, the algorithm will only search at the given taxonomy level given by `tax_id`")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = self._create_network(params, inputs)
        helper = ReconHelper()
        helper.attach_task(self)

        if 'biomass_table' in inputs:
            biomass_table = inputs['biomass_table']
            helper.add_biomass_equation_to_network(net, biomass_table)

        if 'medium_table' in inputs:
            medium_table = inputs['medium_table']
            helper.add_medium_to_network(net, medium_table)

        return {"network": net}

    def _create_network(self, params, inputs):
        helper = ReconHelper()
        helper.attach_task(self)
        unique_name = params["unique_name"]
        tax_id = params['tax_id']
        tax_search_method = params['tax_search_method']
        if not tax_search_method:
            tax_search_method = None
        if 'ec_table' in inputs:
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
            raise BadRequestException("A list of EC numbers or a taxonomy ID is required")