
from typing import List, Tuple
from gws_gena.network.network_cobra import NetworkCobra
from ....helper.base_helper import BaseHelper



class ReactionKnockOutHelperV2(BaseHelper):
    """ ReactionKnockOutHelper """

    FLUX_EPSILON = 1e-9

    def knockout_list_of_reactions(
            self, network: NetworkCobra, reactions: List[str],
            ko_delimiter=None, inplace=False) -> Tuple[NetworkCobra, List]:
        """ knockout a list of reactions in a network """

        if inplace:
            new_net = network
        else:
            new_net: NetworkCobra = network.copy()

        all_ids = []
        found_id = []

        if isinstance(reactions, list):
            for rxn_id, rxn in new_net.get_reactions_dict().items():
                rhea_id = rxn.annotation.get("rhea", [])
                ec_number_tab = []
                for enzyme in rxn.annotation['ec-code']:
                    ec_number_tab.append(enzyme)

                for _, ko_id_str in enumerate(reactions):
                    if ko_delimiter:
                        ko_ids = ko_id_str.split(ko_delimiter)
                    else:
                        ko_ids = [ko_id_str]
                    all_ids.extend(ko_ids)

                    for ko_id in ko_ids:
                        if ko_id in [rxn_id, rhea_id, *ec_number_tab]:
                            rxn.lower_bound = -self.FLUX_EPSILON
                            rxn.upper_bound = self.FLUX_EPSILON
                            found_id.append(ko_id)
        else:
            raise Exception("The reactions param must be a list of string")

        # write warnings
        not_found_id = []
        all_ids = list(set(all_ids))
        for ko_id in all_ids:
            if ko_id not in found_id:
                not_found_id.append(ko_id)
                message = f"The KO ID '{ko_id}' is not found. Please check the KO table."
                self.log_warning_message(message)
        return new_net, not_found_id
