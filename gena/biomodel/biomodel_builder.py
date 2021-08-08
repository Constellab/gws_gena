# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.process import Process
from ..network.network import Network
from .biomodel import BioModel
from .context import Context

# ####################################################################
#
# BioModel class
#
# ####################################################################


class BioModelBuilder(Process):
    input_specs = { 'network': (Network,), 'context': (Context, None,) }
    output_specs = { 'biomodel': (BioModel,) }
    config_specs = {
        "use_context": {"type": bool, "default": True, "Description": "Set True to use the context, False otherwise."},
    }
    
    def check_before_task(self) -> bool:
        if self.get_param("use_context"):
            if not self.input["context"]:
                return False
        return True

    async def task(self):
        net = self.input["network"]
        bio = BioModel()
        bio.add_network(net)
        if self.get_param("use_context"):
            ctx = self.input["context"]
            bio.add_context(ctx, related_network=net)
        self.output["biomodel"] = bio
