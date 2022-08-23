# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import BadRequestException, Table, Task

from ..flat_twin import FlatTwin
from ..twin import Twin

# ####################################################################
#
# TwinAnnotator class
#
# ####################################################################


class TwinAnnotatorHelper():

    @staticmethod
    def annotate(twin: Twin, fba_result: 'FBAResult'):
        if isinstance(twin, FlatTwin):
            raise BadRequestException("Cannot annotate a FlatTwin. A non-flat Twin is required")

        flat_twin: FlatTwin = twin.flatten()
        flux_rev_mapping = flat_twin.reverse_mapping
        annotated_twin = Twin()
        for net in twin.networks.values():
            ctx_name = twin.network_contexts[net.name]
            ctx = twin.contexts[ctx_name]
            for rnx_id in net.reactions.get_elements():
                rxn = net.reactions[rnx_id]
                net_name = net.name
                flat_rxn_id = flux_rev_mapping[net_name][rnx_id]
                fluxes = fba_result.get_flux_dataframe_by_reaction_ids([flat_rxn_id])
                rxn.add_data_slot(
                    "flux_estimates",
                    {
                        "values": [fluxes.at[flat_rxn_id, "value"]],
                        "lower_bounds": [fluxes.at[flat_rxn_id, "lower_bound"]],
                        "upper_bounds": [fluxes.at[flat_rxn_id, "upper_bound"]],
                        "labels": [],
                    }
                )
            annotated_twin.add_network(net, related_context=ctx)
        return annotated_twin
