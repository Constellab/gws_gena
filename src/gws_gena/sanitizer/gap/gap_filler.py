
from gws_core import (
    ConfigParams,
    ConfigSpecs,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    StrParam,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingStyle,
    task_decorator,
)

from ...network.network import Network
from .helper.gap_filler_helper import GapFillerHelper


@task_decorator("GapFiller", human_name="Gap filler", short_description="Fills gaps in networks",
                style=TypingStyle.material_icon(material_icon_name="auto_fix_high", background_color="#d9d9d9"))
class GapFiller(Task):
    """
    GapFiller class.

    This process iteratively fills gaps related to dead-end compounds using the biota DB.
    A gap is detected if a steady compound is a dead-end compound.
    """

    input_specs = InputSpecs({
        'network': InputSpec(Network, human_name="Network", short_description="The network to gap-fill")
    })

    output_specs = OutputSpecs({
        'network': OutputSpec(Network, human_name="Network", short_description="The gap-filled network")
    })

    config_specs = ConfigSpecs({
        'tax_id':
        StrParam(
            default_value=None, human_name="Taxonomy ID",
            short_description="The taxonomy id used to fill gaps (Warning: Not active)")
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = inputs["network"]
        tax_id = params["tax_id"]

        helper = GapFillerHelper()
        helper.attach_message_dispatcher(self.message_dispatcher)
        # net = helper.fill_gaps(net, tax_id=tax_id)
        net = helper.fill_gaps(net)

        return {'network': net}
