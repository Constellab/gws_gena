# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, InputSpec,
                      OutputSpec, StrParam, Task, TaskInputs,
                      TaskOutputs, task_decorator)

from ...network.network import Network
from .helper.gap_filler_helper import GapFillerHelper


@task_decorator("GapFiller", human_name="Fast gap filler", short_description="Fills gaps in a networks")
class GapFiller(Task):
    """
    GapFiller class.

    This process iteratively fills gaps related to dead-end compounds using the biota DB.
    A gap is detected if a steady compound is a dead-end compound.
    """

    input_specs = {
        'network': InputSpec(Network, human_name="Network", short_description="The network to gap-fill")
    }

    output_specs = {
        'network': OutputSpec(Network, human_name="Network", short_description="The gap-filled network")
    }

    config_specs = {
        'tax_id':
        StrParam(
            default_value=None, human_name="Taxonomy ID",
            short_description="The taxonomy id used to fill gaps")
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = inputs["network"]
        tax_id = params["tax_id"]

        helper = GapFillerHelper()
        helper.attach_task(self)
        net = helper.fill_gaps(net, tax_id=tax_id)

        return {'network': net}
