# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws.logger import Error
from gws.utils import slugify
from gws.json import *

from biota.compound import Compound as BiotaCompound

def slugify_id(_id):
    return slugify(_id, snakefy=True, to_lower=False)
    
flattening_delimiter = ":"

# ####################################################################
#
# Compound class
#
# ####################################################################

class Compound:
    """
    Class that represents a network compound. 
    
    Network compounds are proxy of biota compounds (i.e. Chebi compounds). 
    They a used to build reconstructed digital twins. 

    :property id: The id of the compound
    :type id: `str`
    :property name: The name of the compound
    :type name: `str`
    :property charge: The charge of the compound
    :type charge: `str`
    :property mass: The mass of the compound
    :type mass: `str`
    :property monoisotopic_mass: The monoisotopic mass of the compound
    :type monoisotopic_mass: `str`
    :property formula: The formula of the compound
    :type formula: `str`
    :property inchi: The inchi of the compound
    :type inchi: `str`
    :property compartment: The compartment of the compound
    :type compartment: `str`
    :property compartment: The compartment of the compound
    :type compartment: `str`
    :property chebi_id: The corresponding ChEBI id of the compound
    :type chebi_id: `str`
    :property kegg_id: The corresponding Kegg id of the compound
    :type kegg_id: `str`
    """
    
    id = None
    name = None
    network = None
    charge = None
    mass = None
    monoisotopic_mass = None
    formula = None
    inchi = None
    compartment = None
    chebi_id = None
    kegg_id = None
    
    COMPARTMENT_CYTOSOL    = "c"
    COMPARTMENT_NUCLEUS    = "n"
    COMPARTMENT_MITOCHONDRION = "m"
    COMPARTMENT_BIOMASS    = "b"
    COMPARTMENT_EXTRACELL  = "e"
    COMPARTMENT_SINK = "s"

    #VALID_COMPARTMENTS     = ["c","n","b","e"]
    COMPARTMENTS = {
        "c": {"name": "cytosol", "is_steady": True},
        "n": {"name": "nucleus", "is_steady": True},
        "m": {"name": "mitochondrion", "is_steady": True},
        "b": {"name": "biomass", "is_steady": False},
        "e": {"name": "extracellular", "is_steady": False},
        "s": {"name": "sink", "is_steady": False},
    }
    COFACTORS = {
        "CHEBI:15378": "hydron",
        "CHEBI:15377": "water",
        "CHEBI:16240": "hydrogen_peroxide",
        "CHEBI:43474": "hydrogenphosphate",
        "CHEBI:33019": "diphosphate_3",
        
        "CHEBI:57540": "NAD_1",
        "CHEBI:57945": "NADH_2",
        "CHEBI:18009": "NADP",
        "CHEBI:16474": "NADPH",
        "CHEBI:58349": "NADP_3",
        "CHEBI:57783": "NADPH_4",
        #"CHEBI:63528": "dTMP_2",
        "CHEBI:35924": "peroxol",
        "CHEBI:30879": "alcohol",
        "CHEBI:456216": "ADP_3",
        "CHEBI:30616": "ATP_4",
        "CHEBI:456215": "AMP",
        
        "CHEBI:57692": "FAD_3",
        "CHEBI:58307": "FADH2_2",
        "CHEBI:58210": "FMN_3",
        "CHEBI:57618": "FMNH2_2",
        
        "CHEBI:28938": "ammonium",
        "CHEBI:15379": "dioxygen",
        "CHEBI:16526": "carbon_dioxide",
        "CHEBI:29108": "ca2+",
        
        #"CHEBI:57287": "coenzyme_A",
        #"CHEBI:57288": "acetyl_CoA_4"
        
        "CHEBI:59789": "S_adenosyl_L_methionine",
        "CHEBI:57856": "S_adenosyl_L_homocysteine",

        "CHEBI:29033": "iron_2",
        "CHEBI:29034": "iron_3",
    }
    
    _flattening_delimiter = flattening_delimiter
    
    def __init__(self, id="", name="", compartment=None, \
                 network:'Network'=None, formula="", \
                 charge="", mass="", monoisotopic_mass="", inchi="", \
                 chebi_id="", kegg_id=""):  
        
        if not compartment:
            compartment = Compound.COMPARTMENT_CYTOSOL

        if len(compartment) == 1:
            if not compartment in self.COMPARTMENTS.keys():
                raise Error("gena.compound.Compound", "__init__", f"Invalid compartment '{compartment}'")
            compartment_suffix = compartment
        else:
            compartment_suffix = compartment.split("_")[-1]
            if not compartment_suffix in self.COMPARTMENTS.keys():
                raise Error("gena.compound.Compound", "__init__", f"Invalid compartment '{compartment}'")

        self.compartment = compartment   

        if id:
            self.id = slugify_id(id)
            is_compartment_found = False
            for c in self.COMPARTMENTS.keys():
                if self.id.endswith("_" + c):
                    is_compartment_found = True
            if not is_compartment_found:
                raise Error("Compound", "__init__", f"Invalid compound id '{self.id}'. No compartment suffix found.")
            #if not is_compartment_found:
            #    self.id = slugify_id(self.id + "_" + compartment_suffix)
            
            # if not self.id.endswith("_" + self.compartment):
            #     raise Error("Compound", "__init__", f"Invalid compound id '{self.id}'. The id suffix must be {self.compartment}.")
        else:
            # try to use chebi compound name if possible
            if not name:
                if chebi_id:
                    try:
                        c = BiotaCompound.get(BiotaCompound.chebi_id == chebi_id)
                        name = c.get_name()
                    except:
                        name = chebi_id
                else:
                    raise Error("gena.compound.Compound", "__init__", "Please provide at least a valid compound id, name or chebi_id")

            self.id = slugify_id(name + "_" + compartment)
        
        if not name:
            name = self.id
            
        if network:
            self.add_to_network(network)
        
        self.name = name
        self.charge = charge
        self.mass = mass
        self.monoisotopic_mass = monoisotopic_mass
        self.formula = formula
        self.inchi = inchi        
        self.chebi_id = chebi_id
        self.kegg_id = kegg_id
        
    # -- A --

    def add_to_network(self, net: 'Network'):  
        """
        Adds the compound to a newtork
        
        :param net: The network
        :type net: `gena.network.Network`
        """
        
        net.add_compound(self)
    
    # -- C --

    @classmethod
    def create_sink_compound(cls, related_compound: 'Compound') -> 'Compound':
        if related_compound.compartment.endswith("_" + Compound.COMPARTMENT_SINK):
            raise Error("Compound", "create_sink_compound", "Cannot add a sink reaction to another sink reaction")
        name = related_compound.name
        network = related_compound.network
        return Compound(
            name=name,
            compartment=Compound.COMPARTMENT_SINK,
            network=network
        )

    # -- F --
    
    @classmethod
    def _flatten_id(cls, id, ctx_name, is_compartment=False) -> str:
        """
        Flattens a compound or compartment id
        
        :param id: The id
        :type id: `str`
        :param ctx_name: The name of the (metabolic, biological, network) context
        :type ctx_name: `str`
        :param is_compartment: True if it is a compartment id, Otherwise it is a compound id
        :type is_compartment: `bool`
        :return: The flattened id
        :rtype: `str`
        """
        
        delim = cls._flattening_delimiter
        skip_list = [ cls.COMPARTMENT_EXTRACELL ]
        for compart in skip_list:
            if id.endswith("_" + compart) or (is_compartment and id == compart):
                return id
        return slugify_id(ctx_name + delim + id.replace(delim,"_"))
     
    @classmethod
    def from_biota(cls, id=None, name=None, biota_compound=None, chebi_id=None, kegg_id=None, compartment=None, network=None) -> 'Compound':
        """
        Create a network compound from a ChEBI of Kegg id
        
        :param biota_compound: The biota compound to use. If not provided, the chebi_id or keeg_id are used to fetch the corresponding compound from the biota db.
        :type biota_compound: `biota.compound.Compound`
        :param chebi_id: The ChEBI id
        :type chebi_id: `str`
        :param kegg_id: The Kegg id
        :type kegg_id: `str`
        :return: The network compound
        :rtype: `gena.compound.Compound`
        """
        
        if not biota_compound:
            try:
                if chebi_id:
                    if isinstance(chebi_id, float) or isinstance(chebi_id, int):
                        chebi_id = f"CHEBI:{chebi_id}"

                    if "CHEBI" not in chebi_id:
                        chebi_id = f"CHEBI:{chebi_id}"

                    comp = BiotaCompound.get(BiotaCompound.chebi_id == chebi_id)
                elif kegg_id:
                    comp = BiotaCompound.get(BiotaCompound.kegg_id == kegg_id)
                else:
                    raise Error("gena.compound.Compound", "from_biota", "Invalid arguments")
            except:
                raise Error("gena.compound.Compound", "from_biota", "Chebi compound not found")
        else:
            comp = biota_compound
        if compartment is None:
            compartment = Compound.COMPARTMENT_CYTOSOL
        if not name:
            name = comp.name
        c = cls(id=id, name=name, compartment=compartment, network=network)
        c.chebi_id = comp.chebi_id
        c.kegg_id = comp.kegg_id
        c.charge = comp.charge
        c.formula = comp.formula
        c.mass = comp.mass
        c.monoisotopic_mass = comp.monoisotopic_mass
        return c

    # -- I --
 
    @property
    def is_intracellular(self)->bool:
        """
        Test if the compound is intracellular
        
        :return: True if the compound is intracellular, False otherwise
        :rtype: `bool`
        """
        
        compartment_suffix = self.compartment.split("_")[-1]
        return  compartment_suffix != self.COMPARTMENT_EXTRACELL and \
                compartment_suffix != self.COMPARTMENT_BIOMASS and \
                compartment_suffix != self.COMPARTMENT_SINK

    @property
    def is_biomass(self)->bool:
        """
        Test if the compound is the biomass compound
        
        :return: True if the compound is the biomass compound, False otherwise
        :rtype: `bool`
        """

        compartment_suffix = self.compartment.split("_")[-1]
        return compartment_suffix == Compound.COMPARTMENT_BIOMASS

    @property
    def is_sink(self)->bool:
        """
        Test if the compound is a sink compound
        
        :return: True if the compound is a sink compound, False otherwise
        :rtype: `bool`
        """

        compartment_suffix = self.compartment.split("_")[-1]
        return compartment_suffix == Compound.COMPARTMENT_SINK

    @property
    def is_steady(self)->bool:
        """
        Test if the compound is at steady state (is intracellular)
        
        :return: True if the compound is steady, False otherwise
        :rtype: `bool`
        """

        compartment_suffix = self.compartment.split("_")[-1]
        return self.COMPARTMENTS[compartment_suffix]["is_steady"]

    @property
    def is_cofactor(self)->bool:
        """
        Test if the compound is a factor
        
        :return: True if the compound is intracellular, False otherwise
        :rtype: `bool`
        """
        
        return self.chebi_id in self.COFACTORS
    
    # -- R --
    
    def get_related_biota_compound(self):
        """
        Get the biota compound that is related to this network compound
        
        :return: The biota compound corresponding to the chebi of kegg id. Returns `None` is no biota coumpund is found
        :rtype: `bioa.compound.Compound`, `None`
        """
        
        try:
            if self.chebi_id:
                return BiotaCompound.get(BiotaCompound.chebi_id == self.chebi_id)
            elif self.kegg_id:
                return BiotaCompound.get(BiotaCompound.kegg_id == self.kegg_id)
        except:
            return None

    def get_related_biota_reactions(self):
        """
        Get the biota reactions that are related to this network compound
        
        :return: The list of biota reactions corresponding to the chebi of kegg id. Returns [] is no biota reaction is found
        :rtype: `List[bioa.compound.reaction]` or SQL `select` resutls
        """
        
        try:
            if self.chebi_id:
                comp = BiotaCompound.get(BiotaCompound.chebi_id == self.chebi_id)
            elif self.kegg_id:
                comp = BiotaCompound.get(BiotaCompound.kegg_id == self.kegg_id)
            
            return comp.reactions
        except:
            return None

# class SinkCompound(Compound):
    
#     def __init__(self, related_compound: Compound = None):
#         if isinstance(related_compound, SinkCompound):
#             raise Error("SinkCompound", "__init__", "Cannot add a sink reaction to another sink reaction")
#         name = related_compound.name
#         network = related_compound.network
#         super().__init__(
#             name=name,
#             compartment=Compound.COMPARTMENT_SINK,
#             network=network
#         )

#     @classmethod
#     def from_biota(cls, *args, **kwargs):
#         raise Error("SinkReaction", "from_biota", "Not allowed")