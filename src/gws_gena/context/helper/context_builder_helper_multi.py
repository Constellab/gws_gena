# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math
import ast

from gws_core import (BadRequestException, ConfigParams, InputSpec, OutputSpec,
                      Task, TaskInputs, TaskOutputs, task_decorator)

from ...data.flux_table import FluxTable
from ...network.network import Network
from ...network.reaction.reaction import Reaction
from ..context import Context
from ..measure import Measure
from ..typing.measure_typing import MeasureDict
from ..typing.variable_typing import VariableDict
from ..variable import Variable
from ...helper.base_helper import BaseHelper

class ContextBuilderHelperMulti(BaseHelper):
    """
    ContextBuilderHelper

    This helper creates a `Context` object using a `FluxTable` and metabolic `Network`.
    A `Context` object is used to create digital twins and perform metabolic flux analyses.

    - The `FluxTable` gives a list of metabolic fluxes experimentally measured.
    It generally corresponds to the consupmtion or production rates of a list on metabolites measured in a bioreactor.
    - The `Network` is a metabolic network
    """

    input_specs = {'network': InputSpec(Network), 'flux_table': InputSpec(FluxTable)}
    output_specs = {'context': OutputSpec(Context)}
    config_specs = {}

    def build(self, net, flux_table) -> Context:
        ctx = Context()
        targets = flux_table.get_targets()
        ubounds = flux_table.get_upper_bounds()
        lbounds = flux_table.get_lower_bounds()
        scores = flux_table.get_confidence_scores()

        ### TO DO : TESTER SI TOUTES LES SIMULATIONS ONT LA MÊME LONGUEUR sinon mettre message d'erreur + même type
        if isinstance(targets[0], str): #if there is multiple simulations
            for i in range (0,len(targets)):
                targets[i] = ast.literal_eval(targets[i])
                ubounds[i] = ast.literal_eval(ubounds[i])
                lbounds[i] = ast.literal_eval(lbounds[i])
                scores[i] = ast.literal_eval(scores[i])

            for i, ref_id in enumerate(flux_table.get_reaction_ids()):
                if ref_id in net.reactions:
                    for j in range (0,len(ubounds[i])):
                        if ubounds[i][j] < lbounds[i][j]:
                            raise BadRequestException(f"Flux {ref_id} for the simulation {j}: the upper bound must be greater than lower bound")
                        if targets[i][j] < lbounds[i][j]:
                            raise BadRequestException(f"Flux {ref_id} for the simulation {j}: the target must be greater than lower bound")
                        if targets[i][j] > ubounds[i][j]:
                            raise BadRequestException(f"Flux {ref_id} for the simulation {j}: the target must be smaller than upper bound")

                    lbound = lbounds[i]
                    lbound = Reaction.LOWER_BOUND if not lbound else lbound

                    ubound = ubounds[i]
                    ubound = Reaction.UPPER_BOUND if not ubound else ubound

                    score = scores[i]
                    score = 1.0 if not score else score

                    target = targets[i]
                    if not target:
                        target = 0.0
                        score = 0.0  # set the output confidence score to zero if it is NaN

                    measure = Measure(
                        MeasureDict(
                            id="measure_" + ref_id,
                            target=target,
                            upper_bound=ubound,
                            lower_bound=lbound,
                            confidence_score=score,
                            variables=[
                                VariableDict(
                                    coefficient=1.0,
                                    reference_id=ref_id,
                                    reference_type=Variable.REACTION_REFERENCE_TYPE
                                )]
                        ))
                    ctx.add_measure(measure)
                else:
                    raise Exception(f"No reference reaction found with id {ref_id}")

        elif (isinstance(targets[0], float)) : #if there is only one simulation
            for i, ref_id in enumerate(flux_table.get_reaction_ids()):
                if ref_id in net.reactions:
                    if ubounds[i] < lbounds[i]:
                        raise BadRequestException(f"Flux {ref_id}: the upper bound must be greater than lower bound")
                    if targets[i] < lbounds[i]:
                        raise BadRequestException(f"Flux {ref_id}: the target must be greater than lower bound")
                    if targets[i] > ubounds[i]:
                        raise BadRequestException(f"Flux {ref_id}: the target must be smaller than upper bound")

                    lbound = [lbounds[i]]
                    lbound = Reaction.LOWER_BOUND if not lbound else lbound

                    ubound = [ubounds[i]]
                    ubound = Reaction.UPPER_BOUND if not ubound else ubound

                    score = [scores[i]]
                    score = 1.0 if not score else score

                    target = [targets[i]]
                    if not target:
                        target = 0.0
                        score = 0.0  # set the output confidence score to zero if it is NaN

                    measure = Measure(
                        MeasureDict(
                            id="measure_" + ref_id,
                            target=target,
                            upper_bound=ubound,
                            lower_bound=lbound,
                            confidence_score=score,
                            variables=[
                                VariableDict(
                                    coefficient=1.0,
                                    reference_id=ref_id,
                                    reference_type=Variable.REACTION_REFERENCE_TYPE
                                )]
                        ))
                    ctx.add_measure(measure)
                else:
                    raise Exception(f"No reference reaction found with id {ref_id}")

        else:
            raise Exception(f"The target values are not of the correct type. We expected float or string.")


        return ctx
