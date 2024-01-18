# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
import re
from typing import List

from gws_biota import Compound as BiotaCompound
from gws_biota import CompoundLayout as BiotaCompoundLayout
from gws_biota import EnzymeOrtholog as BiotaEnzymeOrtholog
from gws_core import BadRequestException, Logger

from ....helper.base_helper import BaseHelper
from ...compartment.compartment import Compartment
from ...reaction.helper.reaction_biota_helper import ReactionBiotaHelper
from ...typing.compound_typing import CompoundDict
from ...typing.enzyme_typing import EnzymeDict
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

    def _create_compounds_from_dump(
            self, net, data: 'NetworkDict', *, mapping_dict, skip_orphans, translate_ids):
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

            # loads biota info if it exists
            comp_id = comp_data["id"]
            if "compounds" in mapping_dict:
                biota_comp = mapping_dict["compounds"].get(comp_id)
                if biota_comp is not None:
                    for k in comp_data:
                        if hasattr(biota_comp, k):
                            if k != "id":
                                comp_data[k] = getattr(biota_comp, k)

            # create compartment
            compart_id = comp_data["compartment"]
            if compart_id == "":
                # for some bigg models
                # try to infer compartment from compound id
                compart_id = comp_id.split("_")[-1]
                compartment = Compartment.from_biota(bigg_id=compart_id)
                if compartment is None:
                    raise BadRequestException(f"Cannot create compartment '{compart_id}'")
            else:
                compartment = Compartment(data["compartments"][compart_id])

            if translate_ids:
                used_comp_id = None
            else:
                used_comp_id = comp_id

            # create compound
            comp = Compound(
                CompoundDict(
                    id=used_comp_id,
                    name=comp_data.get("name", ""),
                    compartment=compartment,
                    charge=comp_data.get("charge", None),
                    mass=comp_data.get("mass", None),
                    monoisotopic_mass=comp_data.get("monoisotopic_mass", None),
                    formula=comp_data.get("formula", ""),
                    inchi=comp_data.get("inchi", ""),
                    inchikey=comp_data.get("inchikey", ""),
                    chebi_id=comp_data.get("chebi_id", ""),
                    kegg_id=comp_data.get("kegg_id", ""),
                    layout=comp_data.get("layout")
                ))

            if not skip_orphans:
                # add all compounds by default
                try:
                    net.add_compound(comp)
                except Exception as err:
                    raise BadRequestException(f"Cannot compound add {comp_data['id']}. Error: {err}")

            if comp_id not in added_comps:
                added_comps[comp_id] = comp
            else:
                raise BadRequestException(f"Compound id duplicate {comp_id}")

        return net, added_comps

    def _load_all_enzymes(self, data):
        # get all biota enzymes
        ec_numbers = []
        for rxn_data in data["reactions"]:
            if self.is_bigg_data_format:
                skip = False
                for pref in self.BIGG_REACTION_PREFIX_TO_IGNORE:
                    if rxn_data["id"].startswith(pref):
                        skip = True
                        break
                if skip:
                    continue
            ec_numbers.extend(rxn_data["ec_numbers"])
        ec_numbers = list(set(ec_numbers))

        query = BiotaEnzymeOrtholog.select().where(BiotaEnzymeOrtholog.ec_number.in_(ec_numbers))
        biota_enzymes_dict = {}
        rxn_biota_helper = ReactionBiotaHelper()
        rxn_biota_helper.attach_task(self._task)

        enzyme_list: List[EnzymeDict] = rxn_biota_helper.create_reaction_enzyme_dict_from_biota(
            query, load_taxonomy=False, load_pathway=True)

        biota_enzymes_dict = {}
        for val in enzyme_list:
            key = val["ec_number"]
            biota_enzymes_dict[key] = val

        return biota_enzymes_dict

    def _creates_reactions_from_dump(
            self, net, data: 'NetworkDict', *, added_comps, mapping_dict, translate_ids):

        from ...reaction.reaction import Reaction

        ckey = "compounds" if "compounds" in data else "metabolites"
        count = 0
        total_number_of_reactions = len(data["reactions"])
        total_number_of_prints = 3
        rxn_print_interval = int(total_number_of_reactions / total_number_of_prints) or 1

        rxn_biota_helper = ReactionBiotaHelper()
        rxn_biota_helper.attach_task(self._task)

        # load all enzymes if possible
        biota_enzymes_dict = self._load_all_enzymes(data)

        for rxn_data in data["reactions"]:
            count += 1
            if not count % rxn_print_interval:
                perc = int(100 * count/total_number_of_reactions)
                self.log_info_message(f"... {perc}%")

            enzyme_list = []
            for ec_number in rxn_data["ec_numbers"]:
                if ec_number in biota_enzymes_dict:
                    enzyme_list.append(biota_enzymes_dict[ec_number])

            # loads biota info if it exists
            if "reactions" in mapping_dict:
                biota_rxn = mapping_dict["reactions"].get(rxn_data["id"])
                if biota_rxn is not None:
                    rxn_data["rhea_id"] = biota_rxn.rhea_id

            if translate_ids:
                used_rxn_id = None
            else:
                used_rxn_id = rxn_data["id"]

            rxn = Reaction(
                ReactionDict(
                    id=used_rxn_id,
                    name=rxn_data.get("name"),
                    lower_bound=rxn_data.get("lower_bound", Reaction.lower_bound),
                    upper_bound=rxn_data.get("upper_bound", Reaction.upper_bound),
                    enzymes=enzyme_list,
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

            if net.reaction_exists(rxn):
                self.log_warning_message(f"The reaction {rxn.rhea_id} is duplicated. It is only added once.")
            else:
                net.add_reaction(rxn)

        return net

    def _loads_simulations_from_dump(self, net, data: 'NetworkDict'):
        """ Load simulations  """
        if "simulations" in data:
            for vals in data["simulations"]:
                net.add_simulation(vals)
        return net

    def _loads_recon_tags_from_dump(self, net, data: 'NetworkReconTagDict'):
        net.set_recon_tags(data.get("recon_tags", {}))
        return net

    def loads(self, data: 'NetworkDict', *,
              biomass_reaction_id: str = None,
              skip_orphans: bool = False,
              translate_ids: bool = False,
              replace_unknown_compartments: bool = False) -> 'NetworkData':
        """ Load JSON data and create a Network  """
        from ....mapper.bigg_mapper import BiggMapper
        from ...compound.compound import Compound
        from ...network import NetworkData

        data = self._prepare_data(data, replace_unknown_compartments)
        net = NetworkData()

        net.name = data.get("name", NetworkData.DEFAULT_NAME)

        if not data.get("compartments"):
            raise BadRequestException("Invalid network dump. Compartments not found")
        if not data.get("metabolites"):
            raise BadRequestException("Invalid network dump. Metabolites not found")
        if not data.get("reactions"):
            raise BadRequestException("Invalid network dump. Reactions not found")

        mapping_dict = {}
        if translate_ids:
            mapping_dict = BiggMapper.create_mapping_dict(data)

        self.log_info_message("Loading simulations ...")
        net = self._loads_simulations_from_dump(net, data)
        net = self._loads_recon_tags_from_dump(net, data)

        self.log_info_message("Creating compounds ...")
        net, added_comps = self._create_compounds_from_dump(
            net,
            data,
            mapping_dict=mapping_dict,
            skip_orphans=skip_orphans,
            translate_ids=translate_ids
        )

        self.log_info_message("Creating reactions ...")
        net = self._creates_reactions_from_dump(
            net,
            data,
            added_comps=added_comps,
            mapping_dict=mapping_dict,
            translate_ids=translate_ids
        )

        # check if the biomass compartment exists
        if net.get_biomass_compound() is None:
            self.log_warning_message(
                "No explicit biomass entity found. Trying to infer and add an explicit biomass entity ...")
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

    def _prepare_data(self, data, replace_unknown_compartments):
        """ Clean data """
        out_data = copy.deepcopy(data)
        out_data = self._remove_ignored_reactions(out_data)

        out_data["compartments"] = {}
        # prepare compartment

        if isinstance(data["compartments"], dict):
            # -> is bigg data
            for bigg_id in data["compartments"].keys():
                compart = Compartment.from_biota(bigg_id=bigg_id)
                if compart is None:
                    if replace_unknown_compartments:
                        self.log_warning_message(
                            f"The compartment '{bigg_id}' is not known. It is replaced by {compart.bigg_id}.")
                        compart = Compartment.create_other_compartment()
                        bigg_id = compart.bigg_id
                    else:
                        raise BadRequestException(f"The compartment '{bigg_id}' is not known")

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
            if rxn_data.get("enzymes", []):
                rxn_data['ec_numbers'] = [enzyme["ec_number"] for enzyme in rxn_data["enzymes"]]
            elif rxn_data.get("enzyme", {}):
                # TODO:  deprecated to delete later
                rxn_data['ec_numbers'] = [rxn_data["enzyme"]["ec_number"]]
            else:
                rxn_data['ec_numbers'] = []
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
                        ec_numbers = ec_number
                    else:
                        ec_numbers = [ec_number]
                    rxn_data['ec_numbers'] = ec_numbers

        return out_data

    def _remove_ignored_reactions(self, data):
        list_to_keep = []
        for i, rxn_data in enumerate(data["reactions"]):
            to_keep = True
            for pref in self.BIGG_REACTION_PREFIX_TO_IGNORE:
                if rxn_data["id"].startswith(pref):
                    to_keep = False
                    #Constraint the reaction after TO DO  : make an function  + faire que pour les reactions avec le préfixe EX_
                    lower_bound = rxn_data["lower_bound"]
                    upper_bound = rxn_data["upper_bound"]
                    target_metabolite = next(iter(rxn_data["metabolites"]))
                    for reaction in data["reactions"]:
                        if (target_metabolite == "h_e"):
                            break
                        if target_metabolite in reaction["metabolites"] and reaction != rxn_data:
                                for rea in data["reactions"]:
                                    if (rea == reaction):
                                        rea["lower_bound"] = lower_bound
                                        rea["upper_bound"] = upper_bound
                    break
            if to_keep:
                list_to_keep.append(i)

        nb_ignored_rxns = len(data['reactions']) - len(list_to_keep)
        if nb_ignored_rxns > 0:
            self.log_info_message(
                f"{nb_ignored_rxns} reactions with prefixes {self.BIGG_REACTION_PREFIX_TO_IGNORE} were ignored")
            rxn_data = [data["reactions"][i] for i in list_to_keep]
            data["reactions"] = rxn_data

        return data
