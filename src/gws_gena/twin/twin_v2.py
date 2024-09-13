

from gws_core import ResourceSet, TypingStyle, resource_decorator
from gws_gena.network.network_cobra import NetworkCobra
from gws_gena.network.helper.slugify_helper import SlugifyHelper
from ..context.context import Context


@resource_decorator("TwinV2", human_name="TwinV2", short_description="Twin of cell metabolism",
                    style=TypingStyle.material_icon(material_icon_name='hub', background_color='#FFA122'))
class TwinV2(ResourceSet):
    """
    Class that represents a twin.

    A twin is defined by a set of networks related to a set of contexts. It
    can therefore be used for simulation and prediction.
    """
    DEFAULT_NAME = "twin"

    NETWORK_NAME = "network"
    CONTEXT_NAME = "context"

    def __init__(self):
        super().__init__()
        if not self.name:
            self.name = self.DEFAULT_NAME

    def set_network(self, network: NetworkCobra) -> None:
        """
        Set a network to the twin

        :param network: The network to add
        :type network: `gena.network.NetworkCobra`
        """
        if not isinstance(network, NetworkCobra):
            raise Exception("The network must an instance of Network")
        if self.resource_exists(network.name):
            raise Exception(f"Network name '{network.name}' duplicated")

        self.add_resource(network, self.NETWORK_NAME)

    def get_network(self) -> NetworkCobra:
        return self.get_resource(self.NETWORK_NAME)

    def set_context(self, context: Context) -> None:
        """
        Set a context to the twin

        :param context: The context to add
        :type context: `gena.context.Context`
        """
        if not isinstance(context, Context):
            raise Exception("The context must be an instance of Context")
        if self.resource_exists(context.name):
            raise Exception(f'The context "{context.name}" duplicate')

        self.add_resource(context, self.CONTEXT_NAME)

    def get_context(self) -> Context:
        return self.get_resource(self.CONTEXT_NAME)

    def copy(self):
        """ Copy the twin """
        twin = TwinV2()
        twin.set_network(self.get_network().copy())
        twin.set_context(self.get_context().copy())
        return twin

    def set_model_name_twin(self) -> 'TwinV2':
        #Set name model before compounds and metabolites
        modified_twin = TwinV2()
        network = self.get_network().copy()
        context = self.get_context().copy()
        network_name = network.network_dict["id"]
        if network_name is None :
            network_name = network.network_dict["name"]
        #Compartments
        updated_compartments = {} #dict with name compartment and description (id, go id etc)
        compartment_mapping = {} #dict with new and old name compartment
        for compartment_key, description in network.get_compartments().items():
            if description["go_id"] != "GO:0005576":
                new_compartment = SlugifyHelper.slugify_id(network_name + "_" + compartment_key)
                updated_compartments[new_compartment] = description
                compartment_mapping[compartment_key] = new_compartment
            else:
                updated_compartments[compartment_key] = description
                compartment_mapping[compartment_key] = compartment_key
        #Update the compartments of the metabolite in the network
        for metabolite in network.get_metabolites():
            if metabolite.compartment in compartment_mapping:
                metabolite.compartment = compartment_mapping[metabolite.compartment]
        # Update the compartments in the network
        network.set_compartments(updated_compartments)

        #Metabolites
        for metabolite in network.get_metabolites():
            compartment_env_name = network_name + "_" + 'env'
            if metabolite.compartment != compartment_env_name :
                #The metabolite id need to be lower than 256 characters
                if len(network_name + "_" + metabolite.id) > 255 :
                    raise Exception (f"Your metabolite {metabolite.id} is too long. We can't add '{network_name}_' prefix because the total will be {len(network_name + '_' + metabolite.id)} characters. Set a lower name to your metabolite. ")
                else :
                    metabolite.id = network_name + "_" + metabolite.id
        #Reactions
        for reaction in network.get_reactions():
            reaction.id = network_name + "_" + reaction.id

        for measure in context.reaction_data:
            measure_object = context.reaction_data[measure]
            for variable in measure_object.variables:
                variable.reference_id = network_name + "_" + variable.reference_id

        for measure in context.compound_data:
            measure_object = context.compound_data[measure]
            for variable in measure_object.variables: #TODO : checker si cette partie de la boucle fonctionne bien
                metabolite_id = variable.reference_id
                metabolite = network.get_metabolite_by_id_and_check(metabolite_id)
                if not metabolite.compartment == 'env':
                    variable.reference_id = network_name + "_" + variable.reference_id

        modified_twin.set_network(network)
        modified_twin.set_context(context)
        return modified_twin

    # @view(view_type=JSONView, human_name="Summary")
    # def view_as_summary(self, _: ConfigParams) -> JSONView:
    #     """ view as summary """
    #     data = self.get_summary()
    #     j_view = JSONView()
    #     j_view.set_data(data)
    #     return j_view
