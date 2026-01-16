
from gws_core import ResourceSet, TechnicalInfo, TypingStyle, resource_decorator


@resource_decorator("IsolateFinderResult", human_name="Isolate finder result",
                    short_description="Result containing the lists of compounds and reactions that are not connected to cell growth",
                    style=TypingStyle.material_icon(material_icon_name='manage_search', background_color='#ECCD4E'))
class IsolateFinderResult(ResourceSet):
    """
    IsolateFinderResult

    Result containing the lists of compounds and reactions that are not connected to cell growth
    """

    REACTION_TABLE_NAME = "Growth-unconnected reactions"
    COMPOUND_TABLE_NAME = "Growth-unconnected compounds"

    def get_compound_table(self):
        """ Get the table of compounds not connected to growth """
        return self.get_resource(self.COMPOUND_TABLE_NAME)

    def get_reaction_table(self):
        """ Get the table of reactions not connected to growth """
        return self.get_resource(self.REACTION_TABLE_NAME)

    def set_compound_table(self, table):
        """ Set the table of compounds not connected to growth """
        table.name = self.COMPOUND_TABLE_NAME
        self.add_resource(table)
        self.add_technical_info(TechnicalInfo(self.COMPOUND_TABLE_NAME, table.nb_rows))

    def set_reaction_table(self, table):
        """ Set the table of reactions not connected to growth """
        table.name = self.REACTION_TABLE_NAME
        self.add_resource(table)
        self.add_technical_info(TechnicalInfo(self.REACTION_TABLE_NAME, table.nb_rows))
