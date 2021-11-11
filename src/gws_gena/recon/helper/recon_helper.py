# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math

from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import Taxonomy as BiotaTaxo
from gws_core import (BadRequestException, ConfigParams, Logger, Task,
                      TaskInputs)

from ...data.biomass_table import BiomassTable
from ...data.ec_table import ECTable
from ...data.medium_table import MediumTable
from ...network.compound import Compound
from ...network.network import Network, ReactionDuplicate
from ...network.reaction import Reaction


class ReconHelper:

    @classmethod
    def add_biomass_equation_to_network(cls, net: Network, biomass_table: BiomassTable):
        biomass_comps = cls._create_biomass_compounds(net, biomass_table)
        cls._create_biomass_rxns(net, biomass_comps, biomass_table)

    @classmethod
    def create_network_with_taxonomy(cls, tax_id: str, tax_search_method: str, running_task: Task = None) -> Network:
        try:
            tax = BiotaTaxo.get(BiotaTaxo.tax_id == tax_id)
        except Exception as err:
            raise BadRequestException(f"No taxonomy found with tax_id {tax_id}") from err

        enzymes = BiotaEnzyme.select(BiotaEnzyme.ec_number.distinct()).where(
            getattr(BiotaEnzyme, "tax_"+tax.rank) == tax.tax_id,
        )

        if running_task is not None:
            total_enzymes = len(enzymes)
            running_task.log_info_message(f"{total_enzymes} enzymes found")
            net = Network()
            counter = 1
            nb_interval = int(total_enzymes/10) + 1
            perc = 0
            running_task.update_progress_value(perc, message=f"enzyme {counter} ...")

        for enzyme in enzymes:
            if running_task is not None:
                if (counter % nb_interval) == 0:
                    perc = 100*(counter/total_enzymes)
                    enzymes.update_progress_value(perc, message=f"enzyme {counter} ...")
                counter += 1

            try:
                Reaction.from_biota(ec_number=enzyme.ec_number, network=net,
                                    tax_id=tax_id, tax_search_method=tax_search_method)
            except Exception as err:
                pass
                # net.set_reaction_tag(enzyme.ec_number, {
                #     "ec_number": enzyme.ec_number,
                #     "error": str(err)
                # })

        return net

    @classmethod
    def create_network_with_ec_table(
            cls, ec_table: ECTable, tax_id: str, tax_search_method: str, running_task: Task = None) -> Network:
        ec_list = ec_table.get_ec_numbers(rtype="list")
        net = Network()

        if running_task is not None:
            total_enzymes = len(ec_list)
            running_task.log_info_message(f"{total_enzymes} enzymes to process")
            counter = 1
            nb_interval = int(total_enzymes/10) + 1
            perc = 0
            running_task.update_progress_value(perc, message=f"enzyme {counter} ...")

        for ec in ec_list:
            if running_task is not None:
                if (counter % nb_interval) == 0:
                    perc = 100*(counter/total_enzymes)
                    running_task.update_progress_value(perc, message=f"enzyme {counter} ...")
                counter += 1

            ec = str(ec).strip()
            is_incomplete_ec = ("-" in ec)
            if is_incomplete_ec:
                net.set_reaction_tag(ec, {
                    "ec_number": ec,
                    "is_partial_ec_number": True,
                    "error": "Partial ec number"
                })
            else:
                try:
                    Reaction.from_biota(ec_number=ec, network=net, tax_id=tax_id, tax_search_method=tax_search_method)
                except Exception as err:
                    net.set_reaction_tag(ec, {
                        "ec_number": ec,
                        "error": str(err)
                    })

        return net

    @classmethod
    def add_medium_to_network(cls, net: Network, medium_table: MediumTable):
        row_names = medium_table.row_names
        #col_names = medium_table.column_names
        chebi_ids = medium_table.get_chebi_ids()
        i = 0
        for chebi_id in chebi_ids:
            name = row_names[i]
            subs = ReconHelper._retrieve_or_create_comp(net, chebi_id, name, compartment=Compound.COMPARTMENT_EXTRACELL)
            prod = ReconHelper._retrieve_or_create_comp(net, chebi_id, name, compartment=Compound.COMPARTMENT_CYTOSOL)
            try:
                rxn = Reaction(
                    id=prod.name+"_ex",
                    network=net
                )
                rxn.add_product(prod, 1)
                rxn.add_substrate(subs, 1)
            except ReactionDuplicate:
                # ... the reactoin alread exits => OK!
                pass
            except Exception as err:
                raise BadRequestException(f"Cannot create culture medium reactions. Exception: {err}") from err

            i += 1

    @staticmethod
    def _retrieve_or_create_comp(net, chebi_id, name, compartment):
        if not isinstance(chebi_id, str):
            chebi_id = str(chebi_id)
        chebi_id = chebi_id.upper()
        if "CHEBI" not in chebi_id:
            comp = Compound(name=name, compartment=compartment)
        else:
            comp = net.get_compound_by_chebi_id(chebi_id, compartment=compartment)
            if not comp:
                try:
                    comp = Compound.from_biota(chebi_id=chebi_id, compartment=compartment)
                except:
                    # invalid chebi_id
                    comp = Compound(name=name, compartment=compartment)

        if not net.exists(comp):
            net.add_compound(comp)
        net.set_compound_tag(comp.id, {
            "id": comp.id,
            "is_in_biomass_or_medium": True
        })
        return comp

    @classmethod
    def _create_biomass_rxns(cls, net, biomass_comps, biomass_table):
        col_names = biomass_table.column_names
        chebi_col_name = biomass_table.chebi_column_name
        for col_name in col_names:
            if col_name == chebi_col_name:
                continue
            rxn = Reaction(id=col_name, direction="R", lower_bound=0.0)
            coefs = biomass_table.get_column(col_name)
            error_message = "The reaction is empty"
            for i in range(0, len(coefs)):
                if isinstance(coefs[i], str):
                    coefs[i] = coefs[i].strip()
                    if not coefs[i]:
                        continue
                    try:
                        stoich = float(coefs[i])
                    except:
                        error_message = f"Coefficient '{coefs[i]}' is not a valid float"
                        break
                else:
                    if math.isnan(coefs[i]):
                        continue
                    stoich = coefs[i]
                comp = biomass_comps[i]
                if stoich > 0:
                    rxn.add_product(comp, stoich)
                else:
                    rxn.add_substrate(comp, stoich)
            if not rxn.is_empty:
                net.add_reaction(rxn)
            else:
                ec = col_name
                net.set_reaction_tag(ec, {
                    "ec_number": ec,
                    "error": error_message
                })

    @classmethod
    def _create_biomass_compounds(cls, net, biomass_table):
        row_names = biomass_table.row_names
        chebi_ids = biomass_table.get_chebi_ids()
        biomass_col_name = biomass_table.biomass_column_name
        _comps = []
        i = 0
        for chebi_id in chebi_ids:
            name = row_names[i]
            if name == biomass_col_name:
                comp = Compound(name=name, compartment=Compound.COMPARTMENT_BIOMASS)
                _comps.append(comp)
            else:
                comp = cls._retrieve_or_create_comp(net, chebi_id, name, compartment=Compound.COMPARTMENT_CYTOSOL)
                _comps.append(comp)
            i += 1
        if not net.exists(comp):
            net.add_compound(comp)
        return _comps
