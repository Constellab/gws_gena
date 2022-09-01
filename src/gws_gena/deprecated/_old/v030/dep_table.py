from gws_core import File, resource_decorator, exporter_decorator, TableExporter
from ...data.biomass_reaction_table import BiomassReactionTable
from ...data.ec_table import ECTable
from ...data.entity_id_table import EntityIDTable
from ...data.flux_table import FluxTable
from ...data.medium_table import MediumTable

# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

@resource_decorator("BiomassReactionTableFile",
                    human_name="BiomassReactionTableFile",
                    short_description="Stoichiometric table file describing biomass reactions",
                    hide=True, deprecated_since='0.3.1', deprecated_message="Use simple file instead")
class BiomassReactionTableFile(File):
    pass

@resource_decorator("ECTableFile",
                    human_name="ECTableFile",
                    short_description="CSV table file of EC numbers",
                    hide=True, deprecated_since='0.3.1', deprecated_message="Use simple file instead")
class ECTableFile(File):
    pass

@resource_decorator("EntityIDTableFile",
                    human_name="EntityIDTable file",
                    short_description="Generic table file of entity IDs (e.g. CheBI, Rhea IDs, ...)",
                    hide=True, deprecated_since='0.3.1', deprecated_message="Use simple file instead")
class EntityIDTableFile(File):
    pass

@resource_decorator("FluxTableFile",
                    human_name="FluxTable file",
                    short_description="Table file of metabolic flux measurements",
                    hide=True, deprecated_since='0.3.1', deprecated_message="Use simple file instead")
class FluxTableFile(File):
    pass

@resource_decorator("MediumTableFile",
                    human_name="MediumTable file",
                    short_description="Table file of culture medium composition",
                    hide=True, deprecated_since='0.3.1', deprecated_message="Use simple file instead")
class MediumTableFile(File):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################

@exporter_decorator("BiomasssReactionTableExporter",
                    human_name="Biomass reaction table importer",
                    source_type=BiomassReactionTable,
                    hide=True, deprecated_since='0.3.1', deprecated_message="Use simple file exporter instead")
class BiomassReactionTableExporter(TableExporter):
    pass

@exporter_decorator("EntityIDTableExporter", human_name="Entity ID table exporter",
                    source_type=EntityIDTable,
                    hide=True, deprecated_since='0.3.1', deprecated_message="Use simple file exporter instead")
class EntityIDTableExporter(TableExporter):
    pass

@ exporter_decorator("ECTableExporter", human_name="EC number table exporter",
                    source_type=ECTable,
                    hide=True, deprecated_since='0.3.1', deprecated_message="Use simple file exporter instead")
class ECTableExporter(TableExporter):
    pass

@exporter_decorator("FluxTableExporter", human_name="Flux table exporter",
                    source_type=FluxTable,
                    hide=True, deprecated_since='0.3.1', deprecated_message="Use simple file exporter instead")
class FluxTableExporter(TableExporter):
    pass

@exporter_decorator("MediumTableExporter", human_name="Medium table exporter",
                    source_type=MediumTable,
                    hide=True, deprecated_since='0.3.1', deprecated_message="Use simple file exporter instead")
class MediumTableExporter(TableExporter):
    pass
