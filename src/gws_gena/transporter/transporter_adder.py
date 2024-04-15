
from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, Task, TaskInputs, TaskOutputs,
                      task_decorator, TypingStyle)

from ..data.medium_table import MediumTable
from ..network.network import Network
from ..recon.helper.recon_helper import ReconHelper


@task_decorator("TransporterAdder", human_name="Transporter adder", short_description="Transporter adder",
                style=TypingStyle.material_icon(material_icon_name="playlist_add", background_color="#d9d9d9"))
class TransporterAdder(Task):
    """
    Transporter adder task.

    This task involves adding compounds to an existing network. This can be used to add the medium compounds.

    The task will add medium compounds to a network and also create associated medium reactions.

    In input, provide your network and a Medium table (with the name and ChEBI ID of your metabolites).
    In output you will get your extended network.

    """

    input_specs = InputSpecs({
        'network': InputSpec(Network, human_name="The network"),
        'medium_table': InputSpec(MediumTable, human_name="Medium table")
    })
    output_specs = OutputSpecs({'network': OutputSpec(Network)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        helper = ReconHelper()
        helper.attach_task(self)

        net = inputs['network']
        medium_table = inputs['medium_table']

        helper.add_medium_to_network(net, medium_table)

        return {"network": net}
