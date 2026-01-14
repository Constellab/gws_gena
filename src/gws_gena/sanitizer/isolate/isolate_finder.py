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

from ...network.network import Network
from .helper.isolate_finder_helper import IsolateFinderHelper
from .isolate_finder_result import IsolateFinderResult


@task_decorator(
    "IsolateFinder",
    human_name="Isolate finder",
    short_description="Finds genes/reactions that are isolates, i.e. topologically non-connected to the cell growth",
    style=TypingStyle.material_icon(material_icon_name="manage_search", background_color="#d9d9d9"),
)
class IsolateFinder(Task):
    """
    IsolateFinder.

    Determines whether genes/reactions are isolated, i.e. not topologically connected to cell growth.
    """

    input_specs = InputSpecs({"network": InputSpec(Network)})
    output_specs = OutputSpecs({"result": OutputSpec(IsolateFinderResult)})
    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        network: Network = inputs["network"]
        helper = IsolateFinderHelper()
        helper.attach_message_dispatcher(self.message_dispatcher)
        comp_table, rxn_table = helper.find_isolates(network)

        result = IsolateFinderResult()
        result.set_compound_table(comp_table)
        result.set_reaction_table(rxn_table)
        return {"result": result}
