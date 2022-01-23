# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy

from gws_core import (BoolParam, ConfigParams, ListParam, Task, TaskInputs,
                      TaskOutputs, task_decorator)

from ..network.reaction import Reaction
from ..twin.flat_twin import FlatTwin
from ..twin.helper.twin_helper import TwinHelper
from ..twin.twin import Twin
from .twin_efm_table import TwinEFMTable
from .twin_reduction_table import TwinReductionTable


@task_decorator("TwinReducer",
                human_name="Twin reducer",
                short_description="Perform model reduction based on a digital twin")
class TwinReducer(Task):
    """
    Class digital twin reduction
    """

    input_specs = {'twin': (Twin, FlatTwin), }
    output_specs = {
        'efm_table': (TwinEFMTable,),
        'reduction_table': (TwinReductionTable,)
    }
    config_specs = {
        "ignore_cofactors":
        BoolParam(
            default_value=False, human_name="Ignore cofactors",
            short_description="Set True to ignore cofactors, False otherwise."),
        "reversible_reactions":
        ListParam(
            default_value=None, optional=True, human_name="List of reversible reaction",
            short_description="The the list of reversible reactions (EC numbers, Reaction IDs). By default all the reactions are considered irrevesible."), }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
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
                ec_number = rxn.enzyme.get("ec_number")
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
                self.add_warning_message(
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
