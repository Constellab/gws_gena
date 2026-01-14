from gws_core import (
    ConfigParams,
    ConfigSpecs,
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

from ..context.context import Context
from ..network.network import Network
from .twin import Twin

# ####################################################################
#
# Twin class
#
# ####################################################################


@task_decorator(
    "TwinBuilder",
    human_name="Twin builder",
    short_description="Build a digital twin of cell metabolism using a metabolic network and a context",
    style=TypingStyle.material_icon(material_icon_name="build_circle", background_color="#d9d9d9"),
)
class TwinBuilder(Task):
    """TwinBuilder

    Build a digital twin of cell metabolism using a metabolic network and a context
    """

    input_specs = InputSpecs(
        {
            "network": InputSpec(
                Network, human_name="Network", short_description="The metabolic network"
            ),
            "context": InputSpec(
                Context,
                human_name="Context",
                short_description="The metabolic context",
                optional=True,
            ),
        }
    )
    output_specs = OutputSpecs(
        {
            "twin": OutputSpec(
                Twin, human_name="Digital twin", short_description="The digital twin"
            ),
        }
    )

    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = inputs["network"]
        twin = Twin()
        twin.add_network(net)
        if inputs["context"] is not None:
            ctx = inputs["context"]
            twin.add_context(ctx, related_network=net)
        else:
            twin.add_context(Context(), related_network=net)
        return {"twin": twin}
