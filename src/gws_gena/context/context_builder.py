# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BadRequestException, ConfigParams, Task, TaskInputs,
                      TaskOutputs, task_decorator)

from ..data.flux_table import FluxTable
from ..network.network import Network
from .context import Measure, Context, Variable


@task_decorator("ContextBuilder", human_name="Network context builder",
                short_description="Build a context of metabolic network using a flux table")
class ContextBuilder(Task):
    input_specs = {'network': Network, 'flux_table': FluxTable}
    output_specs = {'context': Context}
    config_specs = {}

    async def run(self, _: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        ctx = Context()
        flux: FluxTable = inputs["flux_table"]
        net: Network = inputs["network"]
        targets = flux.get_targets()
        ubounds = flux.get_upper_bounds()
        lbounds = flux.get_lower_bounds()
        scores = flux.get_confidence_scores()
        for i, ref_id in enumerate(flux.get_reaction_ids()):
            ref = net.get_reaction_by_id(ref_id)
            ref_type = Variable.REACTION_REFERENCE_TYPE
            if ref is not None:
                if ubounds[i] < lbounds[i]:
                    raise BadRequestException(f"Flux {ref_id}: the lower bound must be greater than upper bound")
                if targets[i] < lbounds[i]:
                    raise BadRequestException(f"Flux {ref_id}: the target must be greater than lower bound")
                if targets[i] > ubounds[i]:
                    raise BadRequestException(f"Flux {ref_id}: the target must be smaller than upper bound")
                measure = Measure(
                    id="measure_" + ref_id,
                    target=float(targets[i]),
                    upper_bound=float(ubounds[i]),
                    lower_bound=float(lbounds[i]),
                    confidence_score=float(scores[i])
                )
                variable = Variable(
                    coefficient=1.0,
                    reference_id=ref_id,
                    reference_type=ref_type
                )
                measure.add_variable(variable)
                ctx.add_measure(measure)
            else:
                self.log_warning_message(f"No reference reaction found with id {ref_id}")
                #raise BadRequestException(f"No reference reaction found with id {ref_id}")

        return {"context": ctx}
