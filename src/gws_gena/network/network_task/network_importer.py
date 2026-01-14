import json

from gws_core import (
    BadRequestException,
    BoolParam,
    ConfigParams,
    ConfigSpecs,
    File,
    ResourceImporter,
    StrParam,
    TypingStyle,
    importer_decorator,
)

from ..network import Network


@importer_decorator(
    "NetworkImporter",
    human_name="Network importer",
    source_type=File,
    target_type=Network,
    supported_extensions=["json"],
    style=TypingStyle.material_icon(
        material_icon_name="cloud_download", background_color="#d9d9d9"
    ),
)
class NetworkImporter(ResourceImporter):
    """Network Importer Task

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

    config_specs: ConfigSpecs = ConfigSpecs(
        {
            "biomass_metabolite_id_user": StrParam(
                default_value="",
                human_name="Biomass metabolite id",
                short_description="The id of the Biomass metabolite",
                optional=True,
            ),
            "add_biomass": BoolParam(
                human_name="Add biomass metabolite",
                default_value=True,
                short_description="Add biomass metabolite in a compartment biomass. Set True if there is no biomass metabolite in your network",
            ),
            "replace_unknown_compartments": BoolParam(
                human_name="Set default compartment as others",
                default_value=False,
                visibility=BoolParam.PROTECTED_VISIBILITY,
                short_description="Set default compartment as others",
            ),
            "skip_orphans": BoolParam(
                human_name="skip orphans compounds",
                default_value=False,
                visibility=BoolParam.PROTECTED_VISIBILITY,
                short_description="Set True to skip orphan compounds",
            ),
        }
    )

    def import_from_path(
        self, source: File, params: ConfigParams, target_type: type[Network]
    ) -> Network:
        """
        Import a network from a repository

        :param source: The source file
        :type source: File
        :returns: the parsed data
        :rtype: any
        """

        net: Network
        skip_orphans = params.get_value("skip_orphans", False)
        replace_unknown_compartments = params.get_value("replace_unknown_compartments", False)
        biomass_metabolite_id_user = params.get_value("biomass_metabolite_id_user", None)
        add_biomass = params.get_value("add_biomass", False)

        # Convert empty string to None for proper validation
        if not biomass_metabolite_id_user or biomass_metabolite_id_user == "":
            biomass_metabolite_id_user = None

        if add_biomass is True and biomass_metabolite_id_user:
            raise Exception(
                "If there is already a biomass metabolite in the network, we can't add one. Set the parameter 'add_biomass' to False"
            )
        if add_biomass is False and not biomass_metabolite_id_user:
            raise Exception(
                "A biomass metabolite must be present in the network. Set the biomass_metabolite_id_user parameter with your metabolite or set add_biomass to True."
            )

        with open(source.path, encoding="utf-8") as fp:
            try:
                data = json.load(fp)
            except Exception as err:
                raise BadRequestException(f"Cannot load JSON file {source.path}.") from err

            if data.get("reactions"):
                # is an unknown dump network (e.g. BiGG database, classical bioinformatics exchange files)
                net = Network.loads(
                    data,
                    skip_orphans=skip_orphans,
                    replace_unknown_compartments=replace_unknown_compartments,
                    biomass_metabolite_id_user=biomass_metabolite_id_user
                    if not add_biomass
                    else None,
                    add_biomass=add_biomass,
                )
            elif data.get("network"):
                # is gws resource
                net = Network.loads(
                    data["network"],
                    skip_orphans=skip_orphans,
                    replace_unknown_compartments=replace_unknown_compartments,
                )
            elif data.get("data", {}).get("network"):
                # is gws old resource [RETRO COMPATIBILTY]
                # TODO: will be deprecated in the future
                net = Network.loads(
                    data["data"]["network"],
                    skip_orphans=skip_orphans,
                    replace_unknown_compartments=replace_unknown_compartments,
                )
            else:
                raise BadRequestException("Invalid network data")

        return net
