# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
import re

from gws_biota import Compound as BiotaCompound
from gws_biota import CompoundLayout as BiotaCompoundLayout
from gws_biota import EnzymeOrtholog as BiotaEnzymeOrtholog
from gws_core import BadRequestException

from ....helper.base_helper import BaseHelper
from ...compartment.compartment import Compartment
from ...reaction.helper.reaction_biota_helper import ReactionBiotaHelper
from ...typing.compound_typing import CompoundDict
from ...typing.reaction_typing import ReactionDict


class NetworkDataLoaderHelper(BaseHelper):
    """ NetworkDataLoaderHelper """

    BIGG_REACTION_PREFIX_TO_IGNORE = ["EX_", "DM_"]
    is_bigg_data_format = False

    def _convert_bigg_annotation_list_to_dict(self, annotation):
        if isinstance(annotation, list):
            annotation_dict = {}
            for annotation_val in annotation:
                k = annotation_val[0]
                v = annotation_val[1]
                if k not in annotation_dict:
                    annotation_dict[k] = []
                if "http" in v:
                    v = v.split("/")[-1]
                annotation_dict[k].append(v)
        return annotation_dict

    def _loads_all_biota_elements_from_dump(self, data: 'NetworkDict'):

        # get all biota compounds
        chebi_id_list = []
        ckey = "compounds" if "compounds" in data else "metabolites"
        for comp_data in data[ckey]:
            chebi_id_list.append(comp_data["chebi_id"])
        chebi_id_list = list(set(chebi_id_list))
        query = BiotaCompound.select().where(BiotaCompound.chebi_id.in_(chebi_id_list))
        # query = BiotaCompound.search_by_chebi_ids(chebi_id_list)
        biota_comps = {}
        for c in query:
            biota_comps[c.chebi_id] = c
        self.log_info_message(f"{len(query)} compounds loaded from BIOTA.")

        # get all biota enzymes
        ec_number_list = []
        for rxn_data in data["reactions"]:
            if self.is_bigg_data_format:
                skip = False
                for pref in self.BIGG_REACTION_PREFIX_TO_IGNORE:
                    if rxn_data["id"].startswith(pref):
                        skip = True
                        break
                if skip:
                    continue
            ec_number_list.extend(rxn_data["ec_number_list"])
        ec_number_list = list(set(ec_number_list))
        query = BiotaEnzymeOrtholog.select().where(BiotaEnzymeOrtholog.ec_number.in_(ec_number_list))
        biota_enzymes_dict = {}
        rxn_biota_helper = ReactionBiotaHelper()
        rxn_biota_helper.attach_task(self._task)
        for e in query:
            enzyme_dict = rxn_biota_helper.create_reaction_enzyme_dict_from_biota(
                e, load_taxonomy=False, load_pathway=True)
            biota_enzymes_dict[e.ec_number] = enzyme_dict

        self.log_info_message(f"{len(query)} enzyme ortholog loaded from BIOTA.")

        return biota_comps, biota_enzymes_dict

    def _create_compounds_from_dump(
            self, net, data: 'NetworkDict', biota_comps, skip_orphans):
        from ...compound.compound import Compound

        added_comps = {}
        ckey = "compounds" if "compounds" in data else "metabolites"

        count = 0
        total_number_of_compounds = len(data[ckey])
        total_number_of_prints = 3
        comp_print_interval = int(total_number_of_compounds / total_number_of_prints) or 1

        for comp_data in data[ckey]:
            count += 1
            if not count % comp_print_interval:
                perc = int(100 * count/total_number_of_compounds)
                self.log_info_message(f"... {perc}%")

            chebi_id = comp_data.get("chebi_id", "")

            # loads biota info
            if chebi_id:
                biota_comp = biota_comps.get(chebi_id)
                if biota_comp is not None:
                    for k in comp_data:
                        if hasattr(biota_comp, k):
                            if k != "id":
                                comp_data[k] = getattr(biota_comp, k)

                    # retreive valid chebi_id and kegg_id information
                    comp_data["inchikey"] = biota_comp.inchikey
                    comp_data["kegg_id"] = biota_comp.kegg_id

            # create compartment
            compart_id = comp_data["compartment"]
            compartment = Compartment(data["compartments"][compart_id])

            # create compound
            comp_id = comp_data["id"]
            comp = Compound(
                CompoundDict(
                    id=comp_id,
                    name=comp_data.get("name", ""),
                    compartment=compartment,
                    charge=comp_data.get("charge", ""),
                    mass=comp_data.get("mass", ""),
                    monoisotopic_mass=comp_data.get("monoisotopic_mass", ""),
                    formula=comp_data.get("formula", ""),
                    inchi=comp_data.get("inchi", ""),
                    inchikey=comp_data.get("inchikey", ""),
                    chebi_id=comp_data.get("chebi_id", chebi_id),
                    kegg_id=comp_data.get("kegg_id", ""),
                    layout=comp_data.get("layout")
                ))

            if not skip_orphans:
                # add all compounds by default
                net.add_compound(comp)
            added_comps[comp_id] = comp

        return net, added_comps

    def _creates_reactions_from_dump(
            self, net, data: 'NetworkDict', *, added_comps, biota_enzymes_dict):

        from ...reaction.reaction import Reaction

        ckey = "compounds" if "compounds" in data else "metabolites"
        count = 0
        total_number_of_reactions = len(data["reactions"])
        total_number_of_prints = 3
        rxn_print_interval = int(total_number_of_reactions / total_number_of_prints) or 1

        rxn_biota_helper = ReactionBiotaHelper()
        rxn_biota_helper.attach_task(self._task)

        for rxn_data in data["reactions"]:
            count += 1
            if not count % rxn_print_interval:
                perc = int(100 * count/total_number_of_reactions)
                self.log_info_message(f"... {perc}%")

            if self.is_bigg_data_format:
                skip = False
                for pref in self.BIGG_REACTION_PREFIX_TO_IGNORE:
                    if rxn_data["id"].startswith(pref):
                        skip = True
                        break
                if skip:
                    continue

            enzyme_dict = {}
            for ec in rxn_data["ec_number_list"]:
                if ec in biota_enzymes_dict:
                    enzyme_dict = biota_enzymes_dict[ec]
                    break

            rxn = Reaction(
                ReactionDict(
                    id=rxn_data["id"],
                    name=rxn_data.get("name"),
                    lower_bound=rxn_data.get("lower_bound", Reaction.lower_bound),
                    upper_bound=rxn_data.get("upper_bound", Reaction.upper_bound),
                    enzyme=enzyme_dict,
                    direction=rxn_data.get("direction", "B"),
                    rhea_id=rxn_data.get("rhea_id", "")
                ))
            rxn.layout = rxn_data.get("layout", {})

            if "data" in rxn_data:
                rxn.set_data(rxn_data.get("data"))
                # @TODO: check data simulations

            for comp_id in rxn_data[ckey]:
                comp = added_comps[comp_id]
                if isinstance(rxn_data[ckey][comp_id], dict):
                    stoich = float(rxn_data[ckey][comp_id].get("stoich"))
                else:
                    stoich = float(rxn_data[ckey][comp_id])  # for retro compatiblity
                if stoich < 0:
                    rxn.add_substrate(comp, stoich, net)
                elif stoich > 0:
                    rxn.add_product(comp, stoich, net)

            net.add_reaction(rxn)

        return net

    def _loads_simulations_from_dump(self, net, data: 'NetworkDict'):
        """ Load simulations  """
        if "simulations" in data:
            for vals in data["simulations"]:
                net.add_simulation(vals)
        return net

    def loads(self, data: 'NetworkDict', *,
              biomass_reaction_id: str = None, skip_orphans: bool = False) -> 'NetworkData':
        """ Load JSON data and create a Network  """
        from ...compound.compound import Compound
        from ...network import NetworkData

        data = self._prepare_data(data)
        net = NetworkData()

        net.name = data.get("name", NetworkData.DEFAULT_NAME)

        if not data.get("compartments"):
            raise BadRequestException("Invalid network dump. Compartments not found")
        if not data.get("metabolites"):
            raise BadRequestException("Invalid network dump. Metabolites not found")
        if not data.get("reactions"):
            raise BadRequestException("Invalid network dump. Reactions not found")

        self.log_info_message("Loading simulations ...")
        net = self._loads_simulations_from_dump(net, data)

        # loads biota info:
        self.log_info_message("Validating data against BIOTA database ...")
        biota_comps, biota_enzymes_dict = self._loads_all_biota_elements_from_dump(data)

        self.log_info_message("Creating compounds ...")
        net, added_comps = self._create_compounds_from_dump(
            net,
            data,
            biota_comps,
            skip_orphans
        )

        self.log_info_message("Creating reactions ...")
        net = self._creates_reactions_from_dump(
            net,
            data,
            added_comps=added_comps,
            biota_enzymes_dict=biota_enzymes_dict
        )

        # check if the biomass compartment exists
        if net.get_biomass_compound() is None:
            self.log_warning_message(
                "No explicit biomass compound found.\nTry inferring the biomass reaction and adding an explicit dummy biomass compound")
            if biomass_reaction_id:
                self.log_warning_message(f'Looking for user biomass reaction "{biomass_reaction_id}" ...')
                if biomass_reaction_id in net.reactions.get_elements():
                    rxn = net.reactions[biomass_reaction_id]
                    biomass = Compound(
                        CompoundDict(
                            name="biomass",
                            compartment=Compartment.create_biomass_compartment()
                        ))
                    rxn.add_product(biomass, 1, net)
                else:
                    raise BadRequestException(f"No reaction found with ID '{biomass_reaction_id}'")
            else:
                self.log_warning_message('No user biomass given')
                biomass = None
                for rxn in net.reactions.values():
                    if "biomass" in rxn.id.lower():
                        # can be used as biomas reaction
                        if biomass is None:
                            biomass = Compound(
                                CompoundDict(
                                    name="biomass",
                                    compartment=Compartment.create_biomass_compartment()
                                ))
                        rxn.add_product(biomass, 1, net)
                        self.log_warning_message(
                            f'Reaction "{rxn.id} ({rxn.name})" was automatically inferred as biomass reaction')

        return net

    def _prepare_data(self, data):
        """ Clean data """
        out_data = copy.deepcopy(data)
        out_data["compartments"] = {}

        # prepare compartment

        if isinstance(data["compartments"], dict):
            # -> is bigg data
            for bigg_id in data["compartments"].keys():
                compart = Compartment.from_biota(bigg_id=bigg_id)
                if compart is None:
                    raise BadRequestException(f"The compartment bigg_id '{bigg_id}' is not known")
                out_data["compartments"][bigg_id] = {
                    "id": bigg_id,
                    "go_id": compart.go_id,
                    "name": compart.name
                }
            # append biomass compartment
            biomass_compart = Compartment.create_biomass_compartment()
            bigg_id = biomass_compart.bigg_id
            out_data["compartments"][bigg_id] = {
                "id": bigg_id,
                "go_id": biomass_compart.go_id,
                "name": biomass_compart.name
            }
        elif isinstance(data["compartments"], list):
            for compart_data in data["compartments"]:
                id_ = compart_data["id"]
                out_data["compartments"][id_] = compart_data
        else:
            raise BadRequestException("Invalid compartment data")

        # prepare compounds
        ckey = "compounds" if "compounds" in data else "metabolites"
        for comp_data in out_data[ckey]:
            chebi_id = comp_data.get("chebi_id", "")
            if chebi_id:
                continue

            # it is maybe a bigg data format
            annotation = comp_data.get("annotation")
            if annotation is None:
                comp_data["chebi_id"] = None
                continue

            self.is_bigg_data_format = True
            if isinstance(annotation, list):
                annotation = self._convert_bigg_annotation_list_to_dict(annotation)

            alt_chebi_ids = annotation.get("chebi", []) or annotation.get("CHEBI", [])
            if isinstance(alt_chebi_ids, str):
                alt_chebi_ids = [alt_chebi_ids]

            master_chebi_id = None
            for id_ in alt_chebi_ids:
                master_chebi_id = BiotaCompoundLayout.retreive_master_chebi_id(id_)
                if master_chebi_id:
                    break

            if master_chebi_id is not None:
                comp_data["chebi_id"] = master_chebi_id
            else:
                if len(alt_chebi_ids) >= 1:
                    comp_data["chebi_id"] = alt_chebi_ids[0]
                else:
                    comp_data["chebi_id"] = None

        # prepare reactions
        for rxn_data in out_data["reactions"]:
            if not rxn_data.get("enzyme", {}):
                rxn_data['ec_number_list'] = []
                annotation = rxn_data.get("annotation")
                if annotation is None:
                    continue

                self.is_bigg_data_format = True
                if isinstance(annotation, list):
                    annotation = self._convert_bigg_annotation_list_to_dict(annotation)

                ec_number = annotation.get("ec-code") or \
                    annotation.get("ec-number") or \
                    annotation.get("EC Number")

                if ec_number:
                    if isinstance(ec_number, list):
                        ec_number_list = ec_number
                    else:
                        ec_number_list = [ec_number]
                    rxn_data['ec_number_list'] = ec_number_list
            else:
                ec_number = rxn_data["enzyme"]["ec_number"]
                rxn_data['ec_number_list'] = [ec_number]

        return out_data
