# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import Reaction as BiotaReaction
from gws_biota import Taxonomy as BiotaTaxo
from gws_core import (BadRequestException, ConfigParams, InputSpec,
                      OutputSpec, StrParam, Task, TaskInputs, TaskOutputs,
                      Utils, task_decorator)

from ..data.biomass_reaction_table import BiomassReactionTable
from ..data.ec_table import ECTable
from ..data.medium_table import MediumTable
from ..network.network import Network
from ..network.reaction import Reaction
from .helper.recon_helper import ReconHelper


@task_decorator("DraftRecon", human_name="Draft recon", short_description="Draft network reconstruction")
class DraftRecon(Task):
    """
    DraftRecon class.

    This process performs a draft reconstruction of the metabolic network using a list of ec numbers.

    * for each `ec_number`, we find all the corresponding enzymes from the biota DB. If the `tax_id` is also given, we only retrieve enzyme that match the `ec_number` and the taxonomy.
      * if enzymes found
        * for each enzyme
          * we add the corresponding reaction to the network
          * continue
      * if no enzyme found
        * if `tax_id` is given and `tax_search_method == bottom_up`, we traverse the taxonomy tree above the `tax_id` of retrieve all the enzymes matching against the `ec_number`.
        * for each enzyme
          * we add the reaction corresponding the lowest taxonomy lever (i.e. closest to `tax_id`)
          * break the current loop
      * continue

    At the end of the process all the possible reactions existing in the biota DB will be added to the draft network.
    """

    input_specs = {
        'ec_table': InputSpec(ECTable, is_optional=True),
        'biomass_table': InputSpec(BiomassReactionTable, is_optional=True),
        'medium_table': InputSpec(MediumTable, is_optional=True)
    }
    output_specs = {'network': OutputSpec(Network)}
    config_specs = {
        'unique_name': StrParam(
            default_value=Utils.generate_random_chars(4), human_name="Network name", short_description="The unique name of the network. Required to uniquely identify taxa in microbial communities"),
        'tax_id': StrParam(
            default_value='', human_name="Taxonomy ID", short_description="The NCBI taxonomy id. For example: `tax_id = 562` for E. Coli"),
        'tax_search_method':
        StrParam(
            default_value='bottom_up', allowed_values=['none', 'bottom_up'], human_name="Taxonomy search method",
            short_description="If 'bottom_up', the algorithm will to traverse the taxonomy tree to search at higher taxonomy levels until a reaction is found. If `none`, the algorithm will only search at the given taxonomy level given by `tax_id`")}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = self._create_network(params, inputs)
        helper = ReconHelper()
        helper.attach(self)

        if 'biomass_table' in inputs:
            biomass_table = inputs['biomass_table']
            helper.add_biomass_equation_to_network(net, biomass_table)

        if 'medium_table' in inputs:
            medium_table = inputs['medium_table']
            helper.add_medium_to_network(net, medium_table)

        return {"network": net}

    def _create_network(self, params, inputs):
        helper = ReconHelper()
        helper.attach(self)
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
