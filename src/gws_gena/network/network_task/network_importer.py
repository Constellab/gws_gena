# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import Type

from gws_core import (BadRequestException, BoolParam, ConfigParams,
                      ConfigSpecs, File, ResourceImporter, importer_decorator,StrParam)

from ..network import Network


@importer_decorator("NetworkImporter", human_name="Network importer", source_type=File,
                    target_type=Network, supported_extensions=["json"])
class NetworkImporter(ResourceImporter):
    """ Network Importer Task

    This Task allows you to import genome-scale metabolic models in Constellab.
    In input, provide your file and you will get a Network in output.

    Be aware that in Constellab:
        - The compartment extracellular space (theoretical supernatant) (GO:0005615) is consider at steady state.
        - The compartment extracellular region (environment) (GO:0005576) is consider at the non-steady state.

    So, if the metabolite can be consumed, you need to set its compartment to the compartment environment (GO:0005576) and create a new metabolite in the extracellular compartment (GO:0005615) and the associated reactions.
    If the metabolite cannot be consumed, leave it in the extracellular compartment.

    If your model comes from the BIGG database, you don't need to modify your model, this task will import it correctly automatically.

    """

    config_specs: ConfigSpecs = {
        "biomass_metabolite_id_user":
        StrParam(
            default_value = "", human_name="Biomass metabolite id", short_description="The id of the Biomass metabolite", optional = True),
        "add_biomass":
        BoolParam(
            human_name="Add biomass metabolite",
            default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Add biomass metabolite in a compartment biomass."),
        "translate_ids":
        BoolParam(
            human_name="Translate all ids",
            default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="If possible, translate all (compound and reaction) (recommended)"),
        "replace_unknown_compartments":
        BoolParam(
            human_name="Set default compartment as others",
            default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Set default compartment as others"),
        "skip_orphans":
        BoolParam(
            human_name="skip orphans compounds",
            default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Set True to skip orphan compounds"),
    }

    def import_from_path(self, source: File, params: ConfigParams, target_type: Type[Network]) -> Network:
        """
        Import a network from a repository

        :param source: The source file
        :type source: File
        :returns: the parsed data
        :rtype: any
        """

        net: Network
        translate_ids = params.get_value("translate_ids", False)
        skip_orphans = params.get_value("skip_orphans", False)
        replace_unknown_compartments = params.get_value("replace_unknown_compartments", False)
        biomass_metabolite_id_user = params.get_value("biomass_metabolite_id_user", None)
        add_biomass = params.get_value("add_biomass", False)

        if (add_biomass is True and biomass_metabolite_id_user):
            raise Exception("If there is already a biomass metabolite in the network, we can't add one. Set the parameter 'add_biomass' to False")
        if (add_biomass is False and not biomass_metabolite_id_user):
            raise Exception("A biomass metabolite must be present in the network. Set the biomass_metabolite_id_user parameter with your meatbolite or set add_biomass to True.")

        with open(source.path, 'r', encoding="utf-8") as fp:
            try:
                data = json.load(fp)
            except Exception as err:
                raise BadRequestException(f"Cannot load JSON file {source.path}.") from err

            if data.get("reactions"):
                # is an unknown dump network (e.g. BiGG database, classical bioinformatics exchange files)
                net = Network.loads(
                    data,
                    skip_orphans=skip_orphans,
                    translate_ids=translate_ids,
                    replace_unknown_compartments=replace_unknown_compartments,
                    biomass_metabolite_id_user = biomass_metabolite_id_user,
                    add_biomass = add_biomass)
            elif data.get("network"):
                # is gws resource
                net = Network.loads(
                    data["network"],
                    skip_orphans=skip_orphans,
                    translate_ids=translate_ids,
                    replace_unknown_compartments=replace_unknown_compartments
                )
            elif data.get("data", {}).get("network"):
                # is gws old resource [RETRO COMPATIBILTY]
                # TODO: will be deprecated in the future
                net = Network.loads(
                    data["data"]["network"],
                    skip_orphans=skip_orphans,
                    translate_ids=translate_ids,
                    replace_unknown_compartments=replace_unknown_compartments
                )
            else:
                raise BadRequestException("Invalid network data")

        return net
