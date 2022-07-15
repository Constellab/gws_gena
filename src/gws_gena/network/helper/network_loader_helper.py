# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import re

from gws_biota import Compound as BiotaCompound
from gws_biota import EnzymeOrtholog as BiotaEnzymeOrtholog
from gws_core import BadRequestException, Logger

from .reaction_biota_helper import ReactionBiotaHelper


class NetworkLoaderHelper:
    """ NetworkLoaderHelper """

    BIGG_REACTION_PREFIX_TO_IGNORE = ["EX_", "DM_"]

    @classmethod
    def _convert_bigg_annotation_list_to_dict(cls, annotation):
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

    @classmethod
    def _extracts_all_ids_from_dump(cls, data: 'NetworkDict'):
        ckey = "compounds" if "compounds" in data else "metabolites"
        is_bigg_data_format = False
        chebi_id_list = []
        ec_number_list = []

        Logger.info(f"{len(data[ckey])} compounds detected.")
        for val in data[ckey]:
            chebi_id = val.get("chebi_id", "")
            is_bigg_data_format = is_bigg_data_format or ("annotation" in val)
            if not chebi_id and is_bigg_data_format:
                annotation = val["annotation"]
                if isinstance(annotation, list):
                    annotation = cls._convert_bigg_annotation_list_to_dict(annotation)
                current_ids = annotation.get("chebi", []) or annotation.get("CHEBI", [])
                if current_ids:
                    if isinstance(current_ids, str):
                        chebi_id_list.append(current_ids)
                    elif isinstance(current_ids, list):
                        chebi_id_list.extend(current_ids)
            else:
                if chebi_id:
                    chebi_id_list.append(chebi_id)

        Logger.info(f"{len(data['reactions'])} reactions detected.")
        for val in data["reactions"]:

            if is_bigg_data_format:
                skip = False
                for pref in cls.BIGG_REACTION_PREFIX_TO_IGNORE:
                    if val["id"].startswith(pref):
                        skip = True
                        break
                if skip:
                    continue

            if is_bigg_data_format:
                annotation = val["annotation"]
                if isinstance(annotation, list):
                    annotation = cls._convert_bigg_annotation_list_to_dict(annotation)
                ec_number = annotation.get(
                    "ec-code") or annotation.get("ec-number") or annotation.get("EC Number")
            else:
                ec_number = val.get("ec-code") or val.get("ec-number") or val.get("ec") or val.get("EC Number")
            if ec_number:
                if isinstance(ec_number, list):
                    ec_number_list.extend(ec_number)
                else:
                    ec_number_list.append(ec_number)

        chebi_id_list = list(set(chebi_id_list))
        ec_number_list = list(set(ec_number_list))
        return chebi_id_list, ec_number_list

    @ classmethod
    def _create_compounds_from_dump(
            cls, net, data: 'NetworkDict', biota_comps, loads_biota_info, skip_orphans):
        from ..compound import Compound

        added_comps = {}
        ckey = "compounds" if "compounds" in data else "metabolites"

        count = 0
        total_number_of_compounds = len(data[ckey])
        total_number_of_prints = 3
        comp_print_interval = int(total_number_of_compounds / total_number_of_prints) or 1

        for val in data[ckey]:
            count += 1
            if not count % comp_print_interval:
                perc = int(100 * count/total_number_of_compounds)
                Logger.info(f"... {perc}%")

            compart = val["compartment"]
            if not compart in net.compartments:
                raise BadRequestException(
                    f"The compartment '{compart}' of the compound '{val['id']}' not declared in the lists of compartments")

            chebi_id = val.get("chebi_id", "")
            inchikey = val.get("inchikey", "")
            is_bigg_data_format = ("annotation" in val)

            alt_chebi_ids = []
            if not chebi_id and not inchikey and is_bigg_data_format:
                annotation = val["annotation"]
                if isinstance(annotation, list):
                    annotation = cls._convert_bigg_annotation_list_to_dict(annotation)

                alt_chebi_ids = annotation.get("chebi", []) or annotation.get("CHEBI", [])
                inchikey = annotation.get("inchi_key", [""])[0]
                if alt_chebi_ids:
                    if isinstance(alt_chebi_ids, str):
                        chebi_id = alt_chebi_ids
                        alt_chebi_ids = []
                    elif isinstance(alt_chebi_ids, list):
                        chebi_id = alt_chebi_ids.pop(0)

            comp_id = val["id"]
            biota_comp = None
            if loads_biota_info:
                for c_id in alt_chebi_ids:
                    biota_comp = biota_comps.get(c_id)
                    for k in val:
                        if hasattr(biota_comp, k):
                            val[k] = getattr(biota_comp, k)

            comp = Compound(
                id=comp_id,
                name=val.get("name", ""),
                compartment=compart,
                charge=val.get("charge", ""),
                mass=val.get("mass", ""),
                monoisotopic_mass=val.get("monoisotopic_mass", ""),
                formula=val.get("formula", ""),
                inchi=val.get("inchi", ""),
                inchikey=val.get("inchikey", ""),
                chebi_id=chebi_id,
                alt_chebi_ids=alt_chebi_ids,
                kegg_id=val.get("kegg_id", ""),
                layout=val.get("layout")
            )

            if not skip_orphans:
                # add all compounds by default
                net.add_compound(comp)
            added_comps[comp_id] = comp

        return net, added_comps, is_bigg_data_format

    @ classmethod
    def _creates_reactions_from_dump(
            cls, net, data: 'NetworkDict', *, added_comps, biota_enzymes, loads_biota_info, is_bigg_data_format,
            skip_bigg_exchange_reactions):

        from ..reaction import Reaction

        ckey = "compounds" if "compounds" in data else "metabolites"
        count = 0
        total_number_of_reactions = len(data["reactions"])
        total_number_of_prints = 3
        rxn_print_interval = int(total_number_of_reactions / total_number_of_prints) or 1

        for val in data["reactions"]:
            count += 1
            if not count % rxn_print_interval:
                perc = int(100 * count/total_number_of_reactions)
                Logger.info(f"... {perc}%")

            if is_bigg_data_format and skip_bigg_exchange_reactions:
                skip = False
                for pref in cls.BIGG_REACTION_PREFIX_TO_IGNORE:
                    if val["id"].startswith(pref):
                        skip = True
                        break
                if skip:
                    continue

            rxn = Reaction(
                id=val["id"],
                name=val.get("name"),
                lower_bound=val.get("lower_bound", Reaction.lower_bound),
                upper_bound=val.get("upper_bound", Reaction.upper_bound),
                enzyme=val.get("enzyme", {}),
                direction=val.get("direction", "B"),
                rhea_id=val.get("rhea_id", "")
            )
            rxn.layout = val.get("layout", {})

            if loads_biota_info:
                if not rxn.enzyme:
                    if is_bigg_data_format:
                        annotation = val["annotation"]
                        if isinstance(annotation, list):
                            annotation = cls._convert_bigg_annotation_list_to_dict(annotation)

                        ec_number = annotation.get(
                            "ec-code") or annotation.get("ec-number") or annotation.get("EC Number")
                    else:
                        ec_number = val.get("ec-code") or val.get("ec-number") or val.get("ec") or val.get("EC Number")

                    if ec_number:
                        if isinstance(ec_number, list):
                            ec_number_list = ec_number
                        else:
                            ec_number_list = [ec_number]

                        biota_enzyme = None
                        for ec in ec_number_list:
                            biota_enzyme = biota_enzymes.get(ec)
                            if biota_enzyme:
                                enzyme_dict = ReactionBiotaHelper.create_reaction_enzyme_dict_from_biota(
                                    biota_enzyme, load_taxonomy=False, load_pathway=True)
                                rxn.set_enzyme(enzyme_dict)
                                break

            if val.get("estimate"):
                rxn.set_estimate(val.get("estimate"))

            reg_exp = re.compile(r"CHEBI\:\d+$")
            for comp_id in val[ckey]:
                comp = added_comps[comp_id]
                # search according to compound ids
                if reg_exp.match(comp_id):
                    comps = net.get_compounds_by_chebi_id(comp_id)
                    # select the compound in the good compartment
                    for c in comps:
                        if c.compartment == comp.compartment:
                            break

                if isinstance(val[ckey][comp_id], dict):
                    stoich = float(val[ckey][comp_id].get("stoich"))
                else:
                    stoich = float(val[ckey][comp_id])  # for retro compatiblity
                if stoich < 0:
                    rxn.add_substrate(comp, stoich)
                elif stoich > 0:
                    rxn.add_product(comp, stoich)

            net.add_reaction(rxn)

        return net

    @ classmethod
    def loads(cls, data: 'NetworkDict', *, skip_bigg_exchange_reactions: bool = True, loads_biota_info: bool = False,
              biomass_reaction_id: str = None, skip_orphans: bool = False) -> 'Network':
        """ Load JSON data and create a Network  """
        from ..compartment import Compartment
        from ..compound import Compound
        from ..network import Network

        net = Network()
        #data = Compartment.clean(data)

        net.name = data.get("name", Network.DEFAULT_NAME)
        net.compartments = data["compartments"]

        if not data.get("compartments"):
            raise BadRequestException("Invalid network dump. Compartments not found")
        if not data.get("metabolites"):
            raise BadRequestException("Invalid network dump. Metabolites not found")
        if not data.get("reactions"):
            raise BadRequestException("Invalid network dump. Reactions not found")

        biota_enzymes = {}
        biota_comps = {}
        if loads_biota_info:
            Logger.info("Loading all compounds and enzymes from biota. This operation may take a while.")
            chebi_id_list, ec_number_list = cls._extracts_all_ids_from_dump(data)
            query = BiotaCompound.select().where(BiotaCompound.chebi_id.in_(chebi_id_list))
            # query = BiotaCompound.search_by_chebi_ids(chebi_id_list)
            for c in query:
                biota_comps[c.chebi_id] = c
            Logger.info(f"{len(query)} compounds loaded from BIOTA.")
            query = BiotaEnzymeOrtholog.select().where(BiotaEnzymeOrtholog.ec_number.in_(ec_number_list))
            for e in query:
                biota_enzymes[e.ec_number] = e
            Logger.info(f"{len(query)} enzyme ortholog found in BIOTA.")

        Logger.info("Creating compounds ...")
        net, added_comps, is_bigg_data_format = cls._create_compounds_from_dump(
            net,
            data,
            biota_comps,
            loads_biota_info,
            skip_orphans
        )

        Logger.info("Creating reactions ...")
        net = cls._creates_reactions_from_dump(
            net,
            data,
            added_comps=added_comps,
            biota_enzymes=biota_enzymes,
            loads_biota_info=loads_biota_info,
            is_bigg_data_format=is_bigg_data_format,
            skip_bigg_exchange_reactions=skip_bigg_exchange_reactions
        )

        # check if the biomass compartment exists
        biomass_compartment: str = Compartment.BIOMASS
        if net.get_biomass_compound() is None:
            Logger.warning(
                "No explicit biomass compound found.\nTry inferring the biomass reaction and adding an explicit dummy biomass compound")
            if biomass_reaction_id:
                Logger.warning(f'Looking for user biomass reaction "{biomass_reaction_id}" ...')
                if biomass_reaction_id in net.reactions:
                    rxn = net.reactions[biomass_reaction_id]
                    biomass = Compound(name="Biomass", compartment=biomass_compartment)
                    rxn.add_product(biomass, 1)
                    net.compartments[biomass_compartment] = Compartment.COMPARTMENTS[biomass_compartment]  # ["name"]
                    net.update_reaction(rxn)
                else:
                    raise BadRequestException(f"No reaction found with ID '{biomass_reaction_id}'")
            else:
                Logger.warning('No user biomass given')
                for rxn in net.reactions.values():
                    if "biomass" in rxn.id.lower():
                        # can be used as biomas reaction
                        biomass = Compound(name="Biomass", compartment=biomass_compartment)
                        rxn.add_product(biomass, 1)
                        net.compartments[biomass_compartment] = Compartment.COMPARTMENTS[biomass_compartment]  # ["name"]
                        net.update_reaction(rxn)
                        Logger.warning(
                            f'Reaction "{rxn.id} ({rxn.name})" was automatically inferred as biomass reaction')
                        break

        return net
