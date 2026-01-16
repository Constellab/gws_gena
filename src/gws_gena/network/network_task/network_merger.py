
from gws_core import (
    ConfigParams,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingStyle,
    task_decorator,
)

from ..helper.network_merger import NetworkMergerHelper
from ..network import Network


@task_decorator("NetworkMerger", human_name="Network merger", short_description="Merge two networks",
                style=TypingStyle.material_icon(material_icon_name="merge", background_color="#d9d9d9"))
class NetworkMerger(Task):
    """
    NetworkMerger class.

    This process merge two networks
    """

    input_specs = InputSpecs({
        'network_1': InputSpec(Network, human_name="Network 1", short_description="The first network"),
        'network_2': InputSpec(Network, human_name="Network 2", short_description="The second network"),
    })
    output_specs = OutputSpecs({'network': OutputSpec(Network, human_name="Merged network",
                                                      short_description="The merged network")})

    def run(self, _: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net1 = inputs['network_1']
        net2 = inputs['network_2']

        merger_helper = NetworkMergerHelper()
        merger_helper.attach_message_dispatcher(self.message_dispatcher)
        net = merger_helper.merge(destination_network=net1, source_network=net2)
        return {'network': net}
