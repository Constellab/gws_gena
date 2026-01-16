
from gws_core import (
    ConfigParams,
    InputSpec,
    InputSpecs,
    OutputSpecs,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingStyle,
    task_decorator,
)

from ...network.network import Network
from ..gap.helper.gap_finder_helper import GapFinderHelper


@task_decorator("OrphanRemover", human_name="Orphan remover",
                short_description="Remove orphan compounds from a network",
                style=TypingStyle.material_icon(material_icon_name="delete_forever", background_color="#d9d9d9"))
class OrphanRemover(Task):
    """
    OrphanRemover.

    Clean a network by removing all orphan compounds
    """

    input_specs = InputSpecs({'network': InputSpec(Network)})
    output_specs = OutputSpecs({'network': InputSpec(Network)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        network: Network = inputs.get("network")
        helper = GapFinderHelper()
        helper.attach_message_dispatcher(self.message_dispatcher)
        orphans = helper.find_orphan_compound_ids(network)
        for comp_id in orphans:
            network.remove_compound(comp_id)
        self.log_info_message(f"{len(orphans)} orphan compounds removed")
        return {"network": network}
