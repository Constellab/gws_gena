# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BadRequestException
from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs

from ..network.network import Network
from ..data.flux_table import FluxTable
from .twin_context import TwinContext, Variable, Measure

@task_decorator("TwinContextBuilder")
class TwinContextBuilder(Task):
    input_specs = { 'network': (Network,), 'flux_table': (FluxTable,) }
    output_specs = { 'context': (TwinContext,) }
    config_specs = { }
    
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        ctx = TwinContext()
        flux = inputs["flux_table"]
        net = inputs["network"]
        targets = flux.get_targets()
        ubounds = flux.get_upper_bounds()
        lbounds = flux.get_lower_bounds()
        scores = flux.get_confidence_scores()
        i = 0
        for ref_id in flux.row_names:
            ref = net.get_reaction_by_id(ref_id)
            ref_type = Variable.REACTION_REFERENCE_TYPE

            #if not ref:
            #    ref = net.get_compound_by_id(ref_id)
            #    ref_type = Variable.METABOLITE_REFERENCE_TYPE

            if not ref:
                raise BadRequestException(f"No reference reaction found with id {ref_id}")
        
            if ubounds[i] < lbounds[i]:
                raise BadRequestException(f"Flux {ref_id}: the lower bound must be greater than upper bound")
                
            if targets[i] < lbounds[i]:
                raise BadRequestException(f"Flux {ref_id}: the target must be greater than lower bound")
                
            if targets[i] > ubounds[i]:
                raise BadRequestException(f"Flux {ref_id}: the target must be smaller than upper bound")
            
            m = Measure(
                id = "measure_" + ref_id,
                target = float(targets[i]),
                upper_bound = float(ubounds[i]),
                lower_bound = float(lbounds[i]),
                confidence_score = float(scores[i])
            )
            v = Variable(
                coefficient = 1.0,
                reference_id = ref_id,
                reference_type = ref_type
            )
            m.add_variable(v)
            ctx.add_measure(m)
            i += 1
            
        return {"context" : ctx}