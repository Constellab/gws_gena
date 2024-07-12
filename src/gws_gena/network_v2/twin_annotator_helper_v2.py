
from typing import List

from gws_gena.fba.fba_result import FBAResult
from gws_gena.helper.base_helper import BaseHelper
from gws_gena.network_v2.twin_v2 import TwinV2

# ####################################################################
#
# TwinAnnotator class
#
# ####################################################################


class TwinAnnotatorHelperV2(BaseHelper):

    def annotate_from_fba_results(self, twin: TwinV2, fba_results: List[FBAResult]) -> TwinV2:
        """
        Annotate a twin using from FBAResult
        """

        network = twin.get_network()

        i = 0
        for fba_result in fba_results:
            fluxes = fba_result.get_fluxes_dataframe()

            for reaction_id in network.get_reaction_ids():

                flux_estimates = network.get_reaction_simulation_data(
                    reaction_id)

                flux_estimates[str(i)] = {
                    "value": fluxes.at[reaction_id, "value"],
                    "lower_bound": fluxes.at[reaction_id, "lower_bound"],
                    "upper_bound": fluxes.at[reaction_id, "upper_bound"],
                }

                network.set_reaction_simulation_data(
                    reaction_id, flux_estimates)

            i += 1

        return twin

    def annotate_from_fva_results(self, twin: TwinV2, fva_result: 'FVAResult'):
        """
        Annotate a twin using from FVAResult
        """

        return self.annotate_from_fba_results(twin, fva_result)
