# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math

from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import Reaction as BiotaReaction
from gws_biota import Taxonomy as BiotaTaxo
from gws_core import (BadRequestException, ConfigParams, OptionalIn, StrParam,
                      Task, TaskInputs, TaskOutputs, task_decorator)

from ..data.biomass_reaction_table import BiomassReactionTable
from ..data.ec_table import ECTable
from ..data.medium_table import MediumTable
from ..network.compound import Compound
from ..network.network import CompoundDuplicate, Network, ReactionDuplicate
from ..network.reaction import Reaction
from .helper.recon_helper import ReconHelper


@task_decorator("DraftRecon")
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
        'ec_table': OptionalIn(ECTable,),
        'biomass_table': OptionalIn(BiomassReactionTable),
        'medium_table': OptionalIn(MediumTable)
    }
    output_specs = {'network': (Network,)}
    config_specs = {
        'tax_id': StrParam(
            default_value='', human_name="Taxonomy ID", short_description="The NCBI taxonomy id"),
        'tax_search_method':
        StrParam(
            default_value='bottom_up', human_name="Taxonomy search method",
            short_description="If 'bottom_up', the algorithm will to traverse the taxonomy tree to search in the higher taxonomy levels until a reaction is found. If 'none', the algorithm will only search at the given taxonomy level given by `tax_id`")}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = self._create_network(params, inputs)
        if 'biomass_table' in inputs:
            biomass_table = inputs['biomass_table']
            ReconHelper.add_biomass_equation_to_network(net, biomass_table)

        if 'medium_table' in inputs:
            medium_table = inputs['medium_table']
            ReconHelper.add_medium_to_network(net, medium_table)

        return {"network": net}

    def _create_network(self, params, inputs):
        tax_id = params['tax_id']
        if 'ec_table' in inputs:
            return ReconHelper.create_network_with_ec_table(
                ec_table=inputs['ec_table'],
                tax_id=params['tax_id'],
                tax_search_method=params['tax_search_method'],
                running_task=self
            )
        elif tax_id:
            return ReconHelper.create_network_with_taxonomy(
                tax_id=params['tax_id'],
                tax_search_method=params['tax_search_method'],
                running_task=self
            )
        else:
            raise BadRequestException("A list of EC numbers or a taxonomy ID is required")
