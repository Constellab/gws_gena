# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math

from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import Taxonomy as BiotaTaxo
from gws_core import BadRequestException, Logger

from ...data.biomass_reaction_table import BiomassReactionTable
from ...data.ec_table import ECTable
from ...data.medium_table import MediumTable
from ...helper.base_helper import BaseHelper
from ...network.compartment.compartment import Compartment
from ...network.compound.compound import Compound
from ...network.exceptions.reaction_exceptions import ReactionDuplicate
from ...network.network import Network
from ...network.reaction.reaction import Reaction
from ...network.typing.compound_typing import CompoundDict
from ...network.typing.reaction_typing import ReactionDict


class ReconHelper(BaseHelper):
    """ ReconHelper """

    def add_biomass_equation_to_network(self, net: Network, biomass_table: BiomassReactionTable):
        """ Add the biomass equation to a network """
        biomass_comps = self._create_biomass_compounds(net, biomass_table)
        self._create_biomass_rxns(net, biomass_comps, biomass_table)

    def create_network_with_taxonomy(
            self, unique_name: str, tax_id: str, tax_search_method: str) -> Network:
        """ Create a network related to a given taxonomy level """
        try:
            tax = BiotaTaxo.get(BiotaTaxo.tax_id == tax_id)
        except Exception as err:
            raise BadRequestException(f"No taxonomy found with tax_id {tax_id}") from err

        enzymes = BiotaEnzyme.select(BiotaEnzyme.ec_number.distinct()).where(
            getattr(BiotaEnzyme, "tax_"+tax.rank) == tax.tax_id,
        )

        net = Network()
        net.name = unique_name

        total_enzymes = len(enzymes)
        self.log_info_message(f"{total_enzymes} enzymes found")
        counter = 1
        nb_interval = int(total_enzymes/10) + 1
        perc = 0
        self.update_progress_value(perc, message=f"enzyme {counter} ...")

        for enzyme in enzymes:
            if (counter % nb_interval) == 0:
                perc = 100*(counter/total_enzymes)
                self.update_progress_value(perc, message=f"enzyme {counter} ...")
            counter += 1

            ec_number = enzyme.ec_number
            ec_tag = {
                "ec_number": ec_number,
                "reactions": [],
                "errors": [],
                "is_partial_ec_number": None
            }

            try:
                rxns = Reaction.from_biota(ec_number=ec_number,
                                           tax_id=tax_id, tax_search_method=tax_search_method)
                for rxn in rxns:
                    try:
                        net.add_reaction(rxn)
                    except BadRequestException as err:
                        Logger.debug(f"An non-blocking error occured: {err}")
                        ec_tag["errors"].append(str(err))
            except BadRequestException as _:
                pass
                # net.update_reaction_recon_tag(enzyme.ec_number, {
                #     "ec_number": enzyme.ec_number,
                #     "error": str(err)
                # })
            net.update_reaction_recon_tag(ec_number, ec_tag)

        #We create a copy of the network, each metabolite extra must have a metabolite env
        new_net = net.copy()
        #We parse the compounds of the network
        for compound,info in net.compounds.items():
            if (compound.endswith('_extracellular space (theoretical supernatant)')):
                if (info.compartment.go_id == "GO:0005615"):
                    name_env = compound.rsplit('_', 1)[0]
                    #if the metabolite env doesn't exist in the network, we will create it
                    if (name_env + "_extracellular region (environment)" not in new_net.compounds):
                        #create reaction env
                        reaction_env = Reaction(dict(id="reaction_env_"+ name_env))
                        new_net.add_reaction(reaction_env)
                        reaction_env.add_substrate(info, -1, new_net)
                        #create compound env
                        compound_env= Compound(dict(name=name_env, compartment=Compartment.from_biota(go_id=Compartment.EXTRACELL_REGION_GO_ID)))
                        reaction_env.add_product(compound_env, +1, new_net)

        return new_net

    def create_network_with_ec_table(
            self, unique_name: str, ec_table: ECTable, tax_id: str, tax_search_method: str) -> Network:
        """ Create a network related to a list of EC numbers """
        ec_list = ec_table.get_ec_numbers()
        net = Network()
        net.name = unique_name

        total_enzymes = len(ec_list)
        self.log_info_message(f"{total_enzymes} enzymes to process")
        counter = 1
        nb_interval = int(total_enzymes/10) + 1
        perc = 0
        self.update_progress_value(perc, message=f"enzyme {counter} ...")

        for ec in ec_list:
            ec = str(ec).strip()

            ec_tag = {
                "ec_number": ec,
                "reactions": [],
                "errors": [],
                "is_partial_ec_number": None
            }
            if (counter % nb_interval) == 0:
                perc = 100*(counter/total_enzymes)
                self.update_progress_value(perc, message=f"enzyme {counter} ...")
            counter += 1

            is_incomplete_ec = (not ec) or ("-" in ec)
            if is_incomplete_ec:
                ec_tag["is_partial_ec_number"] = True
                ec_tag["errors"].append("Partial ec number")
            else:
                try:
                    rxns = Reaction.from_biota(ec_number=ec, tax_id=tax_id, tax_search_method=tax_search_method)
                    for rxn in rxns:
                        ec_tag["reactions"].append(rxn.id)

                        rnx_tag = {
                            "id": rxn.id,
                            "original_ec": ec,
                            "errors": []
                        }
                        try:
                            # check that is it not a transferred
                            # for i, enz in enumerate(rxn.enzymes):
                            #     if ec != enz["ec_number"]:
                            #         rxn.enzymes[i]["related_deprecated_enzyme"] = ec
                            #         rnx_tag["errors"].append(f"related_deprecated_enzyme: {ec}")
                            net.add_reaction(rxn)
                        except BadRequestException as err:
                            Logger.debug(f"An non-blocking error occured: {err}")
                            ec_tag["errors"].append(str(err))
                            rnx_tag["errors"].append(str(err))

                        net.update_reaction_recon_tag(rxn.id, rnx_tag)
                except BadRequestException as err:
                    Logger.debug(f"An non-blocking error occured: {err}")
                    ec_tag["errors"].append(str(err))

            net.update_ec_recon_tag(ec, ec_tag)

        #We create a copy of the network, each metabolite extra must have a metabolite env
        new_net = net.copy()
        #We parse the compounds of the network
        for compound,info in net.compounds.items():
            if (compound.endswith('_extracellular space (theoretical supernatant)')):
                if (info.compartment.go_id == "GO:0005615"):
                    name_env = compound.rsplit('_', 1)[0]
                    #if the metabolite env doesn't exist in the network, we will create it
                    if (name_env + "_extracellular region (environment)" not in new_net.compounds):
                        #create reaction env
                        reaction_env = Reaction(dict(id="reaction_env_"+ name_env))
                        new_net.add_reaction(reaction_env)
                        reaction_env.add_substrate(info, -1, new_net)
                        #create compound env
                        compound_env= Compound(dict(name=name_env, compartment=Compartment.from_biota(go_id=Compartment.EXTRACELL_REGION_GO_ID)))
                        reaction_env.add_product(compound_env, +1, new_net)
        return new_net

    def add_medium_to_network(self, net: Network, medium_table: MediumTable):
        """ Add medium compounds to a network """
        entities = medium_table.get_entities()
        chebi_ids = medium_table.get_chebi_ids()
        for i, chebi_id in enumerate(chebi_ids):
            name = entities[i]
            subs = ReconHelper._retrieve_or_create_comp(
                net, chebi_id, name, compartment=Compartment.create_extracellular_region_environment_compartment())
            inter = ReconHelper._retrieve_or_create_comp(
                net, chebi_id, name, compartment=Compartment.create_extracellular_compartment())
            prod = ReconHelper._retrieve_or_create_comp(
                net, chebi_id, name, compartment=Compartment.create_cytosol_compartment())
            try:
                #reaction subs => inter
                rxn = Reaction(ReactionDict(id=inter.name+"_env"))
                rxn.add_product(inter, 1, net)
                rxn.add_substrate(subs, 1, net)
                net.add_reaction(rxn)
                for comp in [subs, inter]:
                    net.update_compound_recon_tag(comp.id, {
                        "id": comp.id,
                        "is_supplemented": True
                    })
                #reaction inter => prod
                rxn = Reaction(ReactionDict(id=prod.name+"_ex"))
                rxn.add_product(prod, 1, net)
                rxn.add_substrate(inter, 1, net)
                net.add_reaction(rxn)
                for comp in [inter, prod]:
                    net.update_compound_recon_tag(comp.id, {
                        "id": comp.id,
                        "is_supplemented": True
                    })

            except ReactionDuplicate:
                # ... the reaction already exits => OK!
                pass
            except Exception as err:
                raise BadRequestException(f"Cannot create culture medium reactions. Exception: {err}") from err

    @ staticmethod
    def _retrieve_or_create_comp(net, chebi_id, name, compartment):
        if not isinstance(chebi_id, str):
            chebi_id = str(chebi_id)
        chebi_id = chebi_id.upper()
        if "CHEBI" not in chebi_id:
            comp = Compound(
                CompoundDict(
                    name=name,
                    compartment=compartment
                ))
        else:
            comps = net.get_compounds_by_chebi_id(chebi_id, compartment=compartment)
            if not comps:
                try:
                    comp = Compound.from_biota(chebi_id=chebi_id, compartment_go_id=compartment.go_id)
                except BadRequestException as _:
                    # invalid chebi_id
                    comp = Compound(
                        CompoundDict(
                            name=name,
                            compartment=compartment
                        ))
            else:
                comp = comps[0]

        return comp

    def _create_biomass_rxns(self, net, biomass_comps, biomass_table):
        col_names = biomass_table.column_names
        chebi_col_name = biomass_table.chebi_column
        entity_column = biomass_table.entity_column
        for col_name in col_names:
            if col_name == chebi_col_name or col_name == entity_column:
                continue
            rxn = Reaction(ReactionDict(id=col_name, direction="R", lower_bound=0.0))
            coefs = biomass_table.get_column_data(col_name)
            error_message = "The reaction is empty"
            for i, coef in enumerate(coefs):
                if isinstance(coef, str):
                    coef = coef.strip()
                    if not coef:
                        continue
                    try:
                        stoich = float(coef)
                    except BadRequestException as _:
                        error_message = f"Coefficient '{coef}' is not a valid float"
                        break
                else:
                    if math.isnan(coef):
                        continue
                    stoich = coef
                comp = biomass_comps[i]
                if stoich > 0:
                    rxn.add_product(comp, stoich, net)
                else:
                    rxn.add_substrate(comp, stoich, net)
            if not rxn.is_empty():
                net.add_reaction(rxn)
            else:
                ec = col_name
                net.update_reaction_recon_tag(ec, {
                    "ec_number": ec,
                    "error": error_message
                })

    def _create_biomass_compounds(self, net, biomass_table):
        entities = biomass_table.get_entities()
        chebi_ids = biomass_table.get_chebi_ids()
        biomass_col_name = biomass_table.biomass_column
        _comps = []
        for i, chebi_id in enumerate(chebi_ids):
            name = entities[i]
            if name == biomass_col_name:
                comp = Compound(
                    CompoundDict(
                        name=name,
                        compartment=Compartment.create_biomass_compartment()
                    ))
                _comps.append(comp)
            else:
                comp = self._retrieve_or_create_comp(
                    net, chebi_id, name, compartment=Compartment.create_cytosol_compartment())
                _comps.append(comp)

        return _comps
