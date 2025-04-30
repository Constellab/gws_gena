
from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, Task, TaskInputs, TaskOutputs,
                      task_decorator, TypingStyle)

from gws_gena.network.network_cobra import NetworkCobra
from gws_gena.twin.twin_v2 import TwinV2
from ..context.context import Context
# ####################################################################
#
# Twin class
#
# ####################################################################


@task_decorator("TwinBuilderV2", human_name="Twin builder V2",
                short_description="Build a digital twin of cell metabolism using a metabolic network and a context",
                style=TypingStyle.material_icon(material_icon_name="build_circle", background_color="#d9d9d9"))
class TwinBuilderV2(Task):
    """ TwinBuilder

    Build a digital twin of cell metabolism using a metabolic network and a context
    """

    input_specs = InputSpecs({
        'network': InputSpec(NetworkCobra, human_name="Network", short_description="The metabolic network"),
        'context': InputSpec(Context, human_name="Context", short_description="The metabolic context", is_optional=True)
    })
    output_specs = OutputSpecs({
        'twin': OutputSpec(TwinV2, human_name="Digital twin", short_description="The digital twin"),
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net = inputs["network"]
        twin = TwinV2()
        twin.set_network(net)
        if inputs.get("context") is not None:
            context = inputs["context"]
            twin.set_context(context)
        else:
            twin.set_context(Context())
        return {"twin": twin}
