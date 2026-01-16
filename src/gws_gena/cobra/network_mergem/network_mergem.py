import json
import os

from gws_core import (
    BoolParam,
    ConfigParams,
    ConfigSpecs,
    File,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    StrParam,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingStyle,
    task_decorator,
)

from ...network.network import Network
from ...network.network_task.network_exporter import NetworkExporter
from ...network.network_task.network_importer import NetworkImporter
from .cobra_env_conda import CobraEnvCondaHelper


@task_decorator("NetworkMergem", human_name="Network mergem",
                short_description="Merge two networks with mergem function", style=TypingStyle.material_icon(
                    material_icon_name="merge", background_color="#d9d9d9"))
class NetworkMergem(Task):
    """
    NetworkMergem class.

    This process merge two networks with the mergem function. This task intelligently merges networks by comparing their IDs from different databases.

    Archana Hari, Arveen Zarrabi, Daniel Lobo,
    mergem: merging, comparing, and translating genome-scale metabolic models using universal identifiers,
    NAR Genomics and Bioinformatics, Volume 6, Issue 1, March 2024, lqae010,
    https://doi.org/10.1093/nargab/lqae010
    """

    input_specs = InputSpecs({
        'network_1': InputSpec((File, Network), human_name="Network 1", short_description="The first network in Json or Network format"),
        'network_2': InputSpec((File, Network), human_name="Network 2", short_description="The second network in Json or Network format"),
    })
    config_specs: ConfigSpecs = ConfigSpecs({
        "keep_objective":
        StrParam(
            default_value="merge", allowed_values=["merge", "1", "2"],
            human_name="Keep objective",
            short_description="Specifies if the objective functions are merged or copied from a single model (1 or 2)"),
        "biomass_metabolite_id_user":
        StrParam(
            default_value="", human_name="Biomass metabolite id",
            short_description="The id of the Biomass metabolite to keep in the merged model",
            optional=True),
        "add_biomass":
        BoolParam(
            human_name="Add biomass metabolite", default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Add biomass metabolite in a compartment biomass to the merged model."),
        "exact_stoichiometry":
        BoolParam(
            human_name="Exact stoichiometry", default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Use exact stoichiometry when merging reactions"),
        "add_annotations":
        BoolParam(
            human_name="Add annotations", default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Add additional metabolite and reaction annotations from mergem dictionaries."),
        "use_proton":
        BoolParam(
            human_name="Consider hydrogen and proton metabolites",
            default_value=False, visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Consider hydrogen and proton metabolites when merging reactions."),
        "trans_to_db":
        StrParam(
            default_value="None",
            allowed_values=["None", "chebi", "metacyc", "kegg", "reactome",
                            "metanetx", "hmdb", "biocyc", "bigg", "seed",
                            "sabiork", "rhea"],
            visibility=StrParam.PROTECTED_VISIBILITY, human_name="Translate ids",
            short_description="Translate metabolite and reaction IDs to a target database")})
    output_specs = OutputSpecs({'network': OutputSpec(Network, human_name="Merged network",
                                                      short_description="The merged network")})

    script_merge = os.path.join(os.path.abspath(
        os.path.dirname(__file__)), "_network_mergem.py")

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        net1 = inputs['network_1']
        net2 = inputs['network_2']
        keep_objective = params["keep_objective"]
        biomass_metabolite_id_user = params["biomass_metabolite_id_user"]
        add_biomass = params["add_biomass"]
        exact_stoichiometry = params["exact_stoichiometry"]
        add_annotations = params["add_annotations"]
        use_proton = params["use_proton"]
        trans_to_db = params["trans_to_db"]

        if isinstance(net1, Network):
            net1_path = self.export_to_json(net1)
        elif net1.is_json():
            net1_path = net1.path
        else:
            raise Exception(
                "Your first model must be a Network or a Json File")

        if isinstance(net2, Network):
            net2_path = self.export_to_json(net2)
        elif net2.is_json():
            net2_path = net2.path
        else:
            raise Exception(
                "Your second model must be a Network or a Json File")

        shell_proxy = CobraEnvCondaHelper.create_proxy(self.message_dispatcher)

        output_path = os.path.join(shell_proxy.working_dir, "model.json")
        result = shell_proxy.run(
            f"python3 {self.script_merge} {net1_path} {net2_path} {keep_objective} {exact_stoichiometry} {add_annotations} {use_proton} {trans_to_db} {output_path}",
            shell_mode=True)
        if result != 0:
            raise Exception(
                "An error occurred while executing the script, please check your input files or follow the error messages.")
        json_file = File(output_path)

        net_mergem = NetworkImporter.call(json_file,
                                          params={"add_biomass": add_biomass,
                                                  "biomass_metabolite_id_user": biomass_metabolite_id_user})

        return {'network': net_mergem}

    def export_to_json(self, network: Network):
        network = NetworkExporter.call(network,
                                       params={'file_name': "network",
                                               'file_format': "json"})
        # Load json file
        with open(network.path, encoding='utf-8') as file:
            data = json.load(file)

        # Add the key 'genes'
        data['genes'] = {}
        # Add the key 'id'
        data['id'] = "model_to_merge"

        # Transform the data
        data["compartments"] = {item['id']: item['name']
                                for item in data["compartments"]}
        # Save the new JSON
        with open(network.path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        return network.path
