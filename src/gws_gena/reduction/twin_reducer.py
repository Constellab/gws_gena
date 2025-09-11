
import copy

from gws_core import (BoolParam, ConfigParams, InputSpec, InputSpecs, ConfigSpecs,
                      ListParam, OutputSpec, OutputSpecs, Task, TaskInputs,
                      TaskOutputs, task_decorator, TypingStyle)

from ..network.reaction.reaction import Reaction
from ..twin.flat_twin import FlatTwin
from ..twin.helper.twin_helper import TwinHelper
from ..twin.twin import Twin
from .twin_efm_table import TwinEFMTable
from .twin_reduction_table import TwinReductionTable
from .twin_reducer_helper import TwinReducerHelper


@task_decorator("TwinReducer", human_name="Twin reducer", short_description="Perform model reduction based on a digital twin",
                style=TypingStyle.material_icon(material_icon_name="device_hub", background_color="#d9d9d9"))
class TwinReducer(Task):
    """
    Class digital twin reduction
    Provide a twin in input and set the parameters to get a table of elementary flux modes and a reduction table.
    """

    input_specs = InputSpecs({
        'twin': InputSpec((Twin, FlatTwin), human_name="Digital twin", short_description="The digital twin to reduce"),
    })
    output_specs = OutputSpecs({
        'efm_table': OutputSpec(TwinEFMTable, human_name="EFM table", short_description="The table of elementary flux modes"),
        'reduction_table': OutputSpec(TwinReductionTable, human_name="Reduction table", short_description="The reduction table"),
    })
    config_specs = ConfigSpecs({
        "ignore_cofactors":
        BoolParam(
            default_value=False, human_name="Ignore cofactors",
            short_description="Set True to ignore cofactors, False otherwise."),
        "reversible_reactions":
        ListParam(
            default_value=None, optional=True, human_name="List of reversible reaction",
            short_description="The list of reversible reactions (EC numbers, Reaction IDs). By default all the reactions are considered irreversible."), })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # At the begginning of the task, we install Java because it is mandatory to use the task Twin Reducer.
        # Java is mandatory to use the task Twin Reducer because this Task uses the package efmtool which is a Java software.
        # Commands are the following:
        # apt update
        # apt -y install default-jdk
        shell_proxy = TwinReducerHelper.create_proxy(self.message_dispatcher)
        java_installed = TwinReducerHelper.install_java(shell_proxy)

        if not java_installed:
            raise Exception("Failed to install Java JDK. Java is required for the efmtool package.")


        twin = inputs["twin"]
        if isinstance(twin, FlatTwin):
            flat_twin: FlatTwin = twin
        else:
            flat_twin: FlatTwin = twin.flatten()

        rev = None
        reversible_reactions = params.get_value("reversible_reactions")
        if reversible_reactions:
            reversible_reactions = list(set(reversible_reactions))
            net = flat_twin.get_flat_network()
            i = 0
            rev = [0]*len(net.reactions)
            rxn: Reaction
            not_found_reactions = copy.deepcopy(reversible_reactions)
            for rxn_id, rxn in net.reactions.items():
                for enzyme in rxn.enzymes:
                    ec_number = enzyme.get("ec_number")
                    if rxn_id in reversible_reactions:
                        rev[i] = 1
                        not_found_reactions.remove(rxn_id)
                        if ec_number in reversible_reactions:
                            not_found_reactions.remove(ec_number)
                    elif ec_number in reversible_reactions:
                        rev[i] = 1
                        not_found_reactions.remove(ec_number)
                i += 1

            if not_found_reactions:
                self.log_warning_message(
                    f"Reversible reactions {not_found_reactions} were not found")

        reduced_matrices = TwinHelper.compute_reduced_matrices(
            flat_twin,
            ignore_cofactors=params.get("ignore_cofactors"),
            reversibilities=rev
        )

        twin_efm_table = TwinEFMTable(data=reduced_matrices["EFM"])
        twin_reduction_table = TwinReductionTable(data=reduced_matrices["K"])

        return {
            'efm_table': twin_efm_table,
            'reduction_table': twin_reduction_table
        }
