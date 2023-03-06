# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, InputSpec, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ...network.network import Network
from ..gap.helper.gap_finder_helper import GapFinderHelper


@task_decorator("OrphanRemover", human_name="Orphan remover",
                short_description="Remove orphan compounds from a network")
class OrphanRemover(Task):
    """
    OrphanRemover.

    Clean a network by removing all orphan compounds
    """

    input_specs = {'network': InputSpec(Network)}
    output_specs = {'network': InputSpec(Network)}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        network: Network = inputs.get("network")
        helper = GapFinderHelper()
        helper.attach_task(self)
        orphans = helper.find_orphan_compound_ids(network)
        for comp_id in orphans:
            network.remove_compound(comp_id)
        self.log_info_message(f"{len(orphans)} orphan compounds removed")
        return {"network": network}
