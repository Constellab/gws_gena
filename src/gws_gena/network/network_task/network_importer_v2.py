
import json
import copy
from typing import Type
from gws_gena.network.typing.network_typing import NetworkDict
from gws_biota import CompoundLayout as BiotaCompoundLayout
from gws_biota import Compartment as BiotaCompartment
from cobra.core import Metabolite

from gws_core import (BadRequestException, BoolParam, ConfigParams,
                      ConfigSpecs, File, ResourceImporter, StrParam,
                      TypingStyle, importer_decorator)
from gws_gena.network.network_cobra import NetworkCobra
from gws_gena.network.compartment.compartment import Compartment

@importer_decorator("NetworkImporterV2", human_name="Network importer v2", source_type=File,
                    target_type=NetworkCobra, supported_extensions=["json"],
                    style=TypingStyle.material_icon(material_icon_name="cloud_download", background_color="#d9d9d9"))
class NetworkImporterV2(ResourceImporter):
    """ Network Importer Task

    This Task allows you to import genome-scale metabolic models in Constellab.
    In input, provide your file and you will get a Network in output.

    In the parameters you need to specify the ID of the metabolite associated with the biomass.
    If you don't have any in your model, set the "Add biomass metabolite" option to True.

    Be aware that in Constellab:
        - The compartment extracellular space (theoretical supernatant) (GO:0005615) is consider at steady state.
        - The compartment extracellular region (environment) (GO:0005576) is consider at the non-steady state.

    So, if the metabolite can be consumed, you need to set its compartment to the compartment environment (GO:0005576)
    and create a new metabolite in the extracellular compartment (GO:0005615) and the associated reactions.
    If the metabolite cannot be consumed, leave it in the extracellular compartment.

    If your model comes from the BIGG database, you don't need to modify your model, this task will import it correctly automatically.

    """
    is_bigg_data_format = False

    config_specs: ConfigSpecs = {
        """"biomass_metabolite_id_user":
        StrParam(
            default_value="", human_name="Biomass metabolite id",
            short_description="The id of the Biomass metabolite", optional=True),
        "add_biomass":
        BoolParam(
            human_name="Add biomass metabolite", default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Add biomass metabolite in a compartment biomass."),"""
        "replace_unknown_compartments":
        BoolParam(
            human_name="Set default compartment as others", default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Set default compartment as others"),
        "skip_orphans":
        BoolParam(
            human_name="skip orphans compounds", default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Set True to skip orphan compounds"), }

    def import_from_path(self, source: File, params: ConfigParams, target_type: Type[NetworkCobra]) -> NetworkCobra:
        """
        Import a network from a repository

        :param source: The source file
        :type source: File
        :returns: the parsed data
        :rtype: any
        """

        net: NetworkCobra
        skip_orphans = params.get_value("skip_orphans", False) #TODO : voir si on remet ça en place
        replace_unknown_compartments = params.get_value(
            "replace_unknown_compartments", False)
        """biomass_metabolite_id_user = params.get_value(
            "biomass_metabolite_id_user", None)
        add_biomass = params.get_value("add_biomass", False)"""

        """if (add_biomass is True and biomass_metabolite_id_user):
            raise Exception(
                "If there is already a biomass metabolite in the network, we can't add one. Set the parameter 'add_biomass' to False")"""
        #TODO EN COURS DE TEST POUR VOIR S'il faut l'enlever ou non

        """if (add_biomass is False and not biomass_metabolite_id_user):
            raise Exception(
                "A biomass metabolite must be present in the network. Set the biomass_metabolite_id_user parameter with your metabolite or set add_biomass to True.")
"""
        with open(source.path, 'r', encoding="utf-8") as fp:
            try:
                data = json.load(fp)
            except Exception as err:
                raise BadRequestException(
                    f"Cannot load JSON file {source.path}.") from err
            if data.get("reactions"):
                # is an unknown dump network (e.g. BiGG database, classical bioinformatics exchange files)
                ##net = self.load_network(data = data, replace_unknown_compartments=replace_unknown_compartments
                #,biomass_metabolite_id_user = biomass_metabolite_id_user, add_biomass = add_biomass)
                net = self.load_network(data = data, replace_unknown_compartments=replace_unknown_compartments)
            elif data.get("network"):
                # is gws resource
                net = NetworkCobra.from_cobra_json(data["network"])
                ##net = self.load_network(data = data["network"], replace_unknown_compartments=replace_unknown_compartments
                ##,biomass_metabolite_id_user = biomass_metabolite_id_user, add_biomass = add_biomass)
                net = self.load_network(data = data["network"], replace_unknown_compartments=replace_unknown_compartments)
            else:
                raise Exception("Invalid network data")
        return net

    def load_network(self, data = None, replace_unknown_compartments: bool =None ) -> 'NetworkCobra' : #,biomass_metabolite_id_user: str = None, add_biomass: bool = False
        """ Load JSON data, prepare data, add biomass and create a NetworkCobra  """
        data = self.prepare_data(
                    data,
                    replace_unknown_compartments=replace_unknown_compartments)
        #If there is no key genes in the model, add an empty one
        if not data.get("genes"):
            data["genes"] = ""
        #If there is no key id in the model, add the name or add "model" as id 
        if not data.get("id") :
            if data.get("name") :
                data["id"] = data["name"]
            else:
                data["id"] = "model"
        net = NetworkCobra.from_cobra_json(data)
        #net = self.manage_biomass(net,biomass_metabolite_id_user = biomass_metabolite_id_user, add_biomass = add_biomass)
        return net

    def manage_biomass(self, net: "NetworkCobra", biomass_metabolite_id_user: str = None, add_biomass: bool = False):
        if biomass_metabolite_id_user != "":
            if not net.has_metabolite(biomass_metabolite_id_user):
                # if the metabolite doesn't exist in the network, raises an error
                raise Exception(f"The metabolite {biomass_metabolite_id_user} doesn't exist in the network.")
            else:
                # Check if the metabolite produced by the reaction is in the biomass compartment
                compartment = net.get_metabolite_by_id_and_check(biomass_metabolite_id_user).compartment
                compartment_go_id = BiotaCompartment.get_by_bigg_id(compartment).go_id
                if compartment_go_id != 'GO:0016049':
                    # If not, raise an Exception
                    raise Exception(f"The metabolite {biomass_metabolite_id_user} must be in the biomass compartment")

                # Check if the metabolite biomass is not used in another reaction as a substrate
                for reaction_id in net.get_reaction_ids():
                    reaction = net.get_reaction_by_id_and_check(reaction_id)
                    # Check if the biomass metabolite is a reactant in the current reaction
                    if biomass_metabolite_id_user in [met.id for met in reaction.reactants]:
                        raise ValueError(
                            f"The metabolite {biomass_metabolite_id_user} can't be used in the reaction {reaction_id}. Verify your biomass_metabolite_id.")

        elif add_biomass:
            if net.get_biomass_metabolite() is None:
                for reaction in net.get_reaction_ids():
                    if "biomass" in reaction.lower():
                        # can be used as biomass reaction
                        biomass = Metabolite(id = "biomass", name="biomass", compartment='b')
                        model = net.get_cobra_model()
                        reaction_cobra = model.reactions.get_by_id(reaction)
                        reaction_cobra.add_metabolites({biomass: 1})
                        self.log_warning_message(
                            f'Reaction "{reaction_cobra.id} ({reaction_cobra.name})" was automatically inferred as biomass reaction')
                        net.set_cobra_model(model)
        return net

    def prepare_data(self, data: 'NetworkDict', *,
              replace_unknown_compartments: bool = False) -> 'NetworkDict':
        """ Clean data """
        out_data = copy.deepcopy(data)

        # prepare compartment
        if isinstance(data["compartments"], dict):
            # -> is bigg data
            for bigg_id in out_data["compartments"].keys():
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
            out_data["compartments"] = {}
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
                annotation = rxn_data.get("annotation")
                if annotation is None:
                    rxn_data['annotation'] = {}
                    rxn_data['annotation']['ec-code'] = ''
                    rxn_data['annotation']['rhea'] = ''
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
                    rxn_data['annotation']['ec-code'] = ec_numbers
                else:
                    rxn_data['annotation']['ec-code'] = ''

                #Set rhea annotation
                if rxn_data['annotation'].get("rhea"):
                    rxn_data['annotation']['rhea'] = rxn_data['annotation'].get("rhea")
                else:
                    rxn_data['annotation']['rhea'] = ''

            if rxn_data.get("gene_reaction_rule"):
                rxn_data["gene_reaction_rule"] = rxn_data.get("gene_reaction_rule")

        return out_data


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
