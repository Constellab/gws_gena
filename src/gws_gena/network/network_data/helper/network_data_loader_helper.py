# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
import re

from gws_biota import Compound as BiotaCompound
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

    def _extracts_all_ids_from_dump(self, data: 'NetworkDict'):
        ckey = "compounds" if "compounds" in data else "metabolites"
        is_bigg_data_format = False
        chebi_id_list = []
        ec_number_list = []

        self.log_info_message(f"{len(data[ckey])} compounds detected.")

        for comp_data in data[ckey]:
            chebi_id = comp_data.get("chebi_id", "")
            is_bigg_data_format = is_bigg_data_format or ("annotation" in comp_data)
            if not chebi_id and is_bigg_data_format:
                annotation = comp_data["annotation"]
                if isinstance(annotation, list):
                    annotation = self._convert_bigg_annotation_list_to_dict(annotation)
                current_ids = annotation.get("chebi", []) or annotation.get("CHEBI", [])
                if current_ids:
                    if isinstance(current_ids, str):
                        chebi_id_list.append(current_ids)
                    elif isinstance(current_ids, list):
                        chebi_id_list.extend(current_ids)
            else:
                if chebi_id:
                    chebi_id_list.append(chebi_id)

        self.log_info_message(f"{len(data['reactions'])} reactions detected.")

        for rxn_data in data["reactions"]:
            if is_bigg_data_format:
                skip = False
                for pref in self.BIGG_REACTION_PREFIX_TO_IGNORE:
                    if rxn_data["id"].startswith(pref):
                        skip = True
                        break
                if skip:
                    continue
            if is_bigg_data_format:
                annotation = rxn_data["annotation"]
                if isinstance(annotation, list):
                    annotation = self._convert_bigg_annotation_list_to_dict(annotation)
                ec_number = annotation.get(
                    "ec-code") or annotation.get("ec-number") or annotation.get("EC Number")
            else:
                ec_number = rxn_data.get(
                    "ec-code") or rxn_data.get("ec-number") or rxn_data.get("ec") or rxn_data.get("EC Number")
            if ec_number:
                if isinstance(ec_number, list):
                    ec_number_list.extend(ec_number)
                else:
                    ec_number_list.append(ec_number)

        chebi_id_list = list(set(chebi_id_list))
        ec_number_list = list(set(ec_number_list))
        return chebi_id_list, ec_number_list

    def _create_compounds_from_dump(
            self, net, data: 'NetworkDict', biota_comps, loads_biota_info, skip_orphans):
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
            inchikey = comp_data.get("inchikey", "")
            is_bigg_data_format = ("annotation" in comp_data)

            alt_chebi_ids = []
            if not chebi_id and not inchikey and is_bigg_data_format:
                annotation = comp_data["annotation"]
                if isinstance(annotation, list):
                    annotation = self._convert_bigg_annotation_list_to_dict(annotation)

                alt_chebi_ids = annotation.get("chebi", []) or annotation.get("CHEBI", [])
                inchikey = annotation.get("inchi_key", [""])[0]
                if alt_chebi_ids:
                    if isinstance(alt_chebi_ids, str):
                        chebi_id = alt_chebi_ids
                        alt_chebi_ids = []
                    elif isinstance(alt_chebi_ids, list):
                        chebi_id = alt_chebi_ids.pop(0)

            comp_id = comp_data["id"]
            if loads_biota_info:
                for c_id in alt_chebi_ids:
                    biota_comp = biota_comps.get(c_id)
                    if biota_comp is not None:
                        for k in comp_data:
                            if hasattr(biota_comp, k):
                                comp_data[k] = getattr(biota_comp, k)

                        # retreive valid chebi_id and kegg_id information
                        comp_data["chebi_id"] = biota_comp.chebi_id
                        comp_data["kegg_id"] = biota_comp.kegg_id

                        break

            # create compartment
            compart_id = comp_data["compartment"]
            compartment = Compartment(data["compartments"][compart_id])

            # create compound
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
                    # alt_chebi_ids=alt_chebi_ids,
                    kegg_id=comp_data.get("kegg_id", ""),
                    layout=comp_data.get("layout")
                ))

            if not skip_orphans:
                # add all compounds by default
                net.add_compound(comp)
            added_comps[comp_id] = comp

        return net, added_comps, is_bigg_data_format

    def _creates_reactions_from_dump(
            self, net, data: 'NetworkDict', *, added_comps, biota_enzymes, loads_biota_info, is_bigg_data_format,
            skip_bigg_exchange_reactions):

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

            if is_bigg_data_format and skip_bigg_exchange_reactions:
                skip = False
                for pref in self.BIGG_REACTION_PREFIX_TO_IGNORE:
                    if rxn_data["id"].startswith(pref):
                        skip = True
                        break
                if skip:
                    continue

            rxn = Reaction(
                ReactionDict(
                    id=rxn_data["id"],
                    name=rxn_data.get("name"),
                    lower_bound=rxn_data.get("lower_bound", Reaction.lower_bound),
                    upper_bound=rxn_data.get("upper_bound", Reaction.upper_bound),
                    enzyme=rxn_data.get("enzyme", {}),
                    direction=rxn_data.get("direction", "B"),
                    rhea_id=rxn_data.get("rhea_id", "")
                ))
            rxn.layout = rxn_data.get("layout", {})

            if loads_biota_info:
                if not rxn.enzyme:
                    if is_bigg_data_format:
                        annotation = rxn_data["annotation"]
                        if isinstance(annotation, list):
                            annotation = self._convert_bigg_annotation_list_to_dict(annotation)

                        ec_number = annotation.get(
                            "ec-code") or annotation.get("ec-number") or annotation.get("EC Number")
                    else:
                        ec_number = rxn_data.get(
                            "ec-code") or rxn_data.get("ec-number") or rxn_data.get("ec") or rxn_data.get("EC Number")

                    if ec_number:
                        if isinstance(ec_number, list):
                            ec_number_list = ec_number
                        else:
                            ec_number_list = [ec_number]

                        biota_enzyme = None
                        for ec in ec_number_list:
                            biota_enzyme = biota_enzymes.get(ec)
                            if biota_enzyme:
                                enzyme_dict = rxn_biota_helper.create_reaction_enzyme_dict_from_biota(
                                    biota_enzyme, load_taxonomy=False, load_pathway=True)
                                rxn.set_enzyme(enzyme_dict)
                                break

            if rxn_data.get("data"):
                rxn.set_data(rxn_data.get("data"))

            reg_exp = re.compile(r"CHEBI\:\d+$")
            for comp_id in rxn_data[ckey]:
                comp = added_comps[comp_id]
                # search according to compound ids
                if reg_exp.match(comp_id):
                    comps = net.get_compounds_by_chebi_id(comp_id)
                    # select the compound in the good compartment
                    for c in comps:
                        if c.compartment.go_id == comp.compartment.go_id:
                            break

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

    def loads(self, data: 'NetworkDict', *, skip_bigg_exchange_reactions: bool = True, loads_biota_info: bool = False,
              biomass_reaction_id: str = None, skip_orphans: bool = False) -> 'NetworkData':
        """ Load JSON data and create a Network  """
        from ...compartment.compartment import Compartment
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

        biota_enzymes = {}
        biota_comps = {}
        if loads_biota_info:
            self.log_info_message("Loading all compounds and enzymes from biota. This operation may take a while.")
            chebi_id_list, ec_number_list = self._extracts_all_ids_from_dump(data)
            query = BiotaCompound.select().where(BiotaCompound.chebi_id.in_(chebi_id_list))
            # query = BiotaCompound.search_by_chebi_ids(chebi_id_list)
            for c in query:
                biota_comps[c.chebi_id] = c
            self.log_info_message(f"{len(query)} compounds loaded from BIOTA.")
            query = BiotaEnzymeOrtholog.select().where(BiotaEnzymeOrtholog.ec_number.in_(ec_number_list))
            for e in query:
                biota_enzymes[e.ec_number] = e
            self.log_info_message(f"{len(query)} enzyme ortholog found in BIOTA.")

        self.log_info_message("Creating compounds ...")
        net, added_comps, is_bigg_data_format = self._create_compounds_from_dump(
            net,
            data,
            biota_comps,
            loads_biota_info,
            skip_orphans
        )

        self.log_info_message("Creating reactions ...")
        net = self._creates_reactions_from_dump(
            net,
            data,
            added_comps=added_comps,
            biota_enzymes=biota_enzymes,
            loads_biota_info=loads_biota_info,
            is_bigg_data_format=is_bigg_data_format,
            skip_bigg_exchange_reactions=skip_bigg_exchange_reactions
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

        return out_data
