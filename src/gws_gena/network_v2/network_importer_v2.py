
import json
from typing import Type

from gws_core import (BadRequestException, BoolParam, ConfigParams,
                      ConfigSpecs, File, ResourceImporter, StrParam,
                      TypingStyle, importer_decorator)
from gws_gena.network_v2.network_cobra import NetworkCobra


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

    So, if the metabolite can be consumed, you need to set its compartment to the compartment environment (GO:0005576) and create a new metabolite in the extracellular compartment (GO:0005615) and the associated reactions.
    If the metabolite cannot be consumed, leave it in the extracellular compartment.

    If your model comes from the BIGG database, you don't need to modify your model, this task will import it correctly automatically.

    """

    config_specs: ConfigSpecs = {
        "biomass_metabolite_id_user":
        StrParam(
            default_value="", human_name="Biomass metabolite id",
            short_description="The id of the Biomass metabolite", optional=True),
        "add_biomass":
        BoolParam(
            human_name="Add biomass metabolite", default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Add biomass metabolite in a compartment biomass."),
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
        skip_orphans = params.get_value("skip_orphans", False)
        replace_unknown_compartments = params.get_value(
            "replace_unknown_compartments", False)
        biomass_metabolite_id_user = params.get_value(
            "biomass_metabolite_id_user", None)
        add_biomass = params.get_value("add_biomass", False)

        if (add_biomass is True and biomass_metabolite_id_user):
            raise Exception(
                "If there is already a biomass metabolite in the network, we can't add one. Set the parameter 'add_biomass' to False")
        if (add_biomass is False and not biomass_metabolite_id_user):
            raise Exception(
                "A biomass metabolite must be present in the network. Set the biomass_metabolite_id_user parameter with your metabolite or set add_biomass to True.")

        with open(source.path, 'r', encoding="utf-8") as fp:
            try:
                data = json.load(fp)
            except Exception as err:
                raise BadRequestException(
                    f"Cannot load JSON file {source.path}.") from err

            net = NetworkCobra.from_cobra_json(data)

        return net
