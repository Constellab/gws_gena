# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import re

from gws_biota import Compound as BiotaCompound
from gws_biota import EnzymeOrtholog as BiotaEnzymeOrtholog
from gws_core import BadRequestException, Task

from ....helper.base_helper import BaseHelper
from ...typing.network_typing import NetworkDict


class NetworkDataDumperHelper(BaseHelper):
    """ NetworkDataDumperHelper """

    def dumps(self, network_data, refresh_layout: bool = False) -> NetworkDict:
        """
        Dumps the network
        """

        met_data = []
        rxn_data = []

        # switch all biomass compounds as majors
        biomass_comps = []
        biomass_rxn = network_data.get_biomass_reaction()
        if biomass_rxn is not None:
            for comp_id in biomass_rxn.substrates:
                comp = network_data.compounds[comp_id]
                biomass_comps.append(comp_id)
                comp.append_biomass_layout()
            for comp_id in biomass_rxn.products:
                comp = network_data.compounds[comp_id]
                biomass_comps.append(comp_id)
                if not comp.is_biomass():
                    comp.append_biomass_layout()

        for _met in network_data.compounds.values():
            met_data.append({
                "id": _met.id,
                "name": _met.name,
                "charge": _met.charge,
                "mass": _met.mass,
                "monoisotopic_mass": _met.monoisotopic_mass,
                "formula": _met.formula,
                "inchi": _met.inchi,
                "is_cofactor": _met.is_cofactor(),
                "level": _met.get_level(),
                "compartment": _met.compartment,
                "chebi_id": _met.chebi_id,
                "kegg_id": _met.kegg_id,
                "layout": _met.get_layout(refresh=refresh_layout),
            })

            if _met.compartment == "e":
                pass
            if _met.compartment == "c":
                pass

        for _rxn in network_data.reactions.values():
            _rxn_met = {}
            for susbtrate in _rxn.substrates.values():
                comp_id = susbtrate.compound.id
                stoich = susbtrate.stoich
                _rxn_met.update({comp_id: -abs(stoich)})

            for product in _rxn.products.values():
                comp_id = product.compound.id
                stoich = product.stoich
                _rxn_met.update({comp_id: abs(stoich)})

            rxn_data.append({
                "id": _rxn.id,
                "name": _rxn.name,
                "enzyme": _rxn.enzyme,
                "rhea_id": _rxn.rhea_id,
                "metabolites": _rxn_met,
                "lower_bound": _rxn.lower_bound,
                "upper_bound": _rxn.upper_bound,
                "layout": {"x": None, "y": None},
                "data": _rxn.data,
                "balance": _rxn.compute_mass_and_charge_balance()
            })

        return NetworkDict(
            name=network_data.name,
            metabolites=met_data,
            reactions=rxn_data,
            compartments=network_data.compartments,
            recon_tags=network_data._recon_tags
        )
