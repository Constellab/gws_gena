# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import re
import copy
from typing import List

from gws_core import BadRequestException, Utils
from gws_biota import Compound as BiotaCompound

def slugify_id(_id):
    return Utils.slugify(_id, snakefy=True, to_lower=False)

# ####################################################################
#
# CompoundPosition class
#
# ####################################################################

class CompoundPosition:
    """ Compount position """
    x: float = None
    y: float = None
    z: float = None

    def copy(self) -> 'CompoundPosition':
        p = CompoundPosition()
        p.x = self.x
        p.y = self.y
        p.z = self.z
        return p

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
    
    id = ""
    name = ""
    network = None
    charge = None
    mass = None
    monoisotopic_mass = None
    formula = ""
    inchi = ""
    compartment = ""
    chebi_id = ""
    alt_chebi_ids: List = None
    kegg_id = ""
    inchikey = ""
    position: CompoundPosition = None
    
    FLATTENING_DELIMITER = "_"
    COMPARTMENT_DELIMITER = "_"
    COMPARTMENT_CYTOSOL    = "c"
    COMPARTMENT_NUCLEUS    = "n"
    COMPARTMENT_MITOCHONDRION = "m"
    COMPARTMENT_BIOMASS    = "b"
    COMPARTMENT_EXTRACELL  = "e"
    COMPARTMENT_SINK = "s"

    # Use BiGG nomenclature for compartments
    COMPARTMENTS = { 
        "c": {"name": "cytosol", "is_steady": True},
        "n": {"name": "nucleus", "is_steady": True},
        "m": {"name": "mitochondrion", "is_steady": True},
        "b": {"name": "biomass", "is_steady": False},
        "e": {"name": "extracellular", "is_steady": False},
        "s": {"name": "sink", "is_steady": False},
        "r": {"name": "endoplasmic reticulum", "is_steady": True},
        "v": {"name": "vacuole", "is_steady": True},
        "x": {"name": "peroxisome/glyoxysome", "is_steady": True},
        "g": {"name": "golgi apparatus", "is_steady": True}
    }

    LEVEL_MAJOR = "major"
    LEVEL_MINOR = "minor"
    LEVEL_COFACTOR = "cofactor"

    COFACTOR_NAME_PATTERNS = ["residue"]
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
        "CHEBI:63528": "dTMP_2",
        "CHEBI:35924": "peroxol",
        "CHEBI:30879": "alcohol",

        "CHEBI:456216": "ADP(3-)",
        "CHEBI:30616": "ATP(4-)",

        "CHEBI:57667": "dADP(3-)",
        "CHEBI:61404": "dATP(4-)",

        "CHEBI:456215": "AMP",
        "CHEBI:60377": "CMP, cytidine 5'-monophosphate(2-)",

        "CHEBI:57692": "FAD_3",
        "CHEBI:58307": "FADH2_2",
        "CHEBI:58210": "FMN_3",
        "CHEBI:57618": "FMNH2_2",
        
        "CHEBI:28938": "ammonium",
        "CHEBI:15379": "dioxygen",
        "CHEBI:16526": "carbon_dioxide",
        "CHEBI:29108": "ca2+",
        
        "CHEBI:57287": "coenzyme A(4-)",
        
        "CHEBI:59789": "S_adenosyl_L_methionine",
        "CHEBI:57856": "S_adenosyl_L_homocysteine",

        "CHEBI:29033": "iron_2",
        "CHEBI:29034": "iron_3",

        "CHEBI:61402": "ITP(4-)",
        "CHEBI:58280": "IDP(3-)",

        "CHEBI:58189": "GDP(3-)",
        "CHEBI:37565": "GTP(4-)",
        "CHEBI:61429": "dGTP(4-)",
        
        "CHEBI:58223": "UDP(3-)",
        "CHEBI:46398": "UTP(4-)",
        "CHEBI:61555": "dUTP(4-)",

        "CHEBI:58280": "IDP(3-)",
        "CHEBI:61402": "ITP(4-)",
        "CHEBI:61382": "dITP(4-)",

        "CHEBI:58069": "CDP(3-)",
        "CHEBI:37563": "CTP(4-)",
        "CHEBI:61481": "dCTP(4-)",

        "CHEBI:58223": "UDP(3-)",
        "CHEBI:46398": "UTP(4-)",
        "CHEBI:61555": "dUTP(4-)",
        
        "CHEBI:16389": "ubiquinones",
        "CHEBI:17976": "ubiquinol",
        "CHEBI:61683": "ubiquinone-8",
        "CHEBI:61682": "ubiquinol-8",
        "CHEBI:24646": "hydroquinones",
        "CHEBI:132124": "1,4-benzoquinones",

        "CHEBI:17499": "hydrogen donor",
        "CHEBI:13193": "hydrogen acceptor",

        "CHEBI:29950": "L-cysteine residue",
        "CHEBI:29969": "L-lysinium residue", 
    }

    MAJOR_NAME_PATTERNS = []
    MAJORS = {
        "CHEBI:17925": "alpha-D-glucose",
        "CHEBI:15903": "beta-D-glucose",
        "CHEBI:58225": "alpha-D-glucose 6-phosphate(2-)",

        "CHEBI:17378": "D-glyceraldehyde",
        "CHEBI:59776": "D-glyceraldehyde 3-phosphate(2-)",
        "CHEBI:16016": "dihydroxyacetone",
        "CHEBI:57642": "glycerone phosphate(2-)",

        "CHEBI:32966": "beta-D-fructofuranose 1,6-bisphosphate(4-)",
        "CHEBI:37721": "fructofuranose",
        "CHEBI:57634": "beta-D-fructofuranose 6-phosphate(2-)",
        "CHEBI:138881": "beta-D-fructofuranose 1-phosphate(2-)",

        "CHEBI:57288": "acetyl_CoA(4-)",

        "CHEBI:15361": "pyruvate",
        "CHEBI:17180": "3-hydroxypyruvate",
        "CHEBI:58702": "phosphonatoenolpyruvate",
        "CHEBI:30089": "acetate",
        "CHEBI:13705": "acetoacetate",
        "CHEBI:16452": "oxaloacetate(2-)",
        "CHEBI:16947": "citrate(3-)",
        "CHEBI:16810": "2-oxoglutarate(2-)",
        "CHEBI:24996": "lactate",
        "CHEBI:16651": "(S)-lactate",
        "CHEBI:16004": "(R)-lactate",
        "CHEBI:15740": "formate",
        "CHEBI:29806": "fumarate(2-)",
        "CHEBI:30031": "succinate(2-)",
        "CHEBI:57292": "succinyl-CoA(5-)",

        "CHEBI:30839": "orotate",

        "CHEBI:10983": "(R)-3-hydroxybutyrate",
        "CHEBI:11047": "(S)-3-hydroxybutyrate",
    
        "CHEBI:32372": "palmitoleate",
        "CHEBI:17268": "myo-inositol",
        "CHEBI:15354": "choline",
        "CHEBI:295975": "choline phosphate(1-)",
        "CHEBI:57643": "1,2-diacyl-sn-glycero-3-phosphocholine",

        "CHEBI:17754": "glycerol",
        "CHEBI:64615": "triacyl-sn-glycerol",
        "CHEBI:17815": "1,2-diacyl-sn-glycerol",
        "CHEBI:58608": "1,2-diacyl-sn-glycerol 3-phosphate(2-)",
        "CHEBI:57262": "3-sn-phosphatidyl-L-serine(1-)",

        "CHEBI:59996": "1,2-diacyl-sn-glycerol 3-diphosphate(3-)",
        "CHEBI:57597": "sn-glycerol 3-phosphate(2-)",

        "CHEBI:16113": "cholesterol",
        "CHEBI:62237": "cardiolipin(2-)",

        "CHEBI:58359": "L-glutamine zwitterion",        
        "CHEBI:29985": "L-glutamate(1-)",
        "CHEBI:60039": "L-proline zwitterion",
        "CHEBI:29991": "L-aspartate(1-)",
        "CHEBI:57844": "L-methionine zwitterion",
        "CHEBI:58048": "L-asparagine zwitterion",
        "CHEBI:57972": "L-alanine zwitterion",
        "CHEBI:57762": "L-valine zwitterion",
        "CHEBI:57427": "L-leucine zwitterion",
        "CHEBI:58045": "L-isoleucine zwitterion",
        "CHEBI:57305": "glycine zwitterion",
        "CHEBI:57926": "L-threonine zwitterion",
        "CHEBI:16467": "L-arginine",
        "CHEBI:33384": "L-serine",

        "CHEBI:16236": "ethanol",
        "CHEBI:17790": "methanol",

        "CHEBI:57880": "1-phosphatidyl-1D-myo-inositol(1-)",

        "CHEBI:16199": "urea",
        "CHEBI:57743": "L-citrulline zwitterion",
        "CHEBI:32682": "L-ornithinium(1+)",
        "CHEBI:32682": "L-argininium(1+)",

        "CHEBI:58273": "aldehydo-D-ribose 5-phosphate(2-)",
        "CHEBI:58121": "D-ribulose 5-phosphate(2-)",
        "CHEBI:57737": "D-xylulose 5-phosphate(2-)",
        "CHEBI:17140": "D-xylulose",
        "CHEBI:57483": "sedoheptulose 7-phosphate(2-)",
        "CHEBI:16897": "D-erythrose 4-phosphate(2-)"
    }

    def __init__(self, id="", name="", compartment=None, \
                 network:'Network'=None, formula="", \
                 charge="", mass="", monoisotopic_mass="", inchi="", \
                 inchikey="", chebi_id="", alt_chebi_ids: List=None, kegg_id=""):  
        
        if chebi_id is None:
            chebi_id = ""
        if inchikey is None:
            inchikey = ""
        if not isinstance(chebi_id, str):
            raise BadRequestException("The chebi_id must be a string")
        if not isinstance(inchikey, str):
            raise BadRequestException("The inchikey must be a string")

        if not compartment:
            compartment = Compound.COMPARTMENT_CYTOSOL

        if len(compartment) == 1:
            if not compartment in self.COMPARTMENTS.keys():
                raise BadRequestException(f"Invalid compartment '{compartment}'")
            compartment_suffix = compartment
        else:
            compartment_suffix = compartment.split(Compound.COMPARTMENT_DELIMITER)[-1]
            if not compartment_suffix in self.COMPARTMENTS.keys():
                raise BadRequestException(f"Invalid compartment '{compartment}'")

        self.compartment = compartment   

        if id:
            self.id = slugify_id(id)
            is_compartment_found = False
            for c in self.COMPARTMENTS.keys():
                if self.id.endswith(Compound.COMPARTMENT_DELIMITER + c):
                    is_compartment_found = True
            if not is_compartment_found:
                raise BadRequestException(f"Invalid compound id '{self.id}'. No compartment suffix found.")
            #if not is_compartment_found:
            #    self.id = slugify_id(self.id + Compound.COMPARTMENT_DELIMITER + compartment_suffix)
            
            if not self.id.endswith(Compound.COMPARTMENT_DELIMITER + compartment_suffix):
                raise BadRequestException(f"Invalid compound id '{self.id}'. The id suffix must be {compartment_suffix}.")
        else:
            # try to use inchikey or chebi compound name if possible
            is_found = False
            if not name:
                if inchikey:
                    try:
                        c = BiotaCompound.get(BiotaCompound.inchikey == inchikey)
                        name = c.get_name()
                        is_found = True
                    except:
                        is_found = False
                
                if not is_found and chebi_id:
                    try:
                        c = BiotaCompound.get(BiotaCompound.chebi_id == chebi_id)
                        name = c.get_name()
                    except:
                        name = chebi_id
                else:
                    raise BadRequestException("Please provide at least a valid compound id, name or chebi_id")

            self.id = slugify_id(name + Compound.COMPARTMENT_DELIMITER + compartment_suffix)
        
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
        self.inchikey = inchikey
        self.chebi_id = chebi_id
        self.kegg_id = kegg_id
        self.alt_chebi_ids = (alt_chebi_ids if alt_chebi_ids else [])
        self.position = CompoundPosition()
        
    # -- A --

    def add_to_network(self, net: 'Network'):  
        """
        Adds the compound to a newtork
        
        :param net: The network
        :type net: `gena.network.Network`
        """
        
        net.add_compound(self)
    
    # -- C --

    def copy(self) -> 'Compound':
        c = Compound( id=self.id )
        c.name = self.name
        c.network = self.network
        c.charge = self.charge
        c.mass = self.mass
        c.monoisotopic_mass = self.monoisotopic_mass
        c.formula = self.formula
        c.inchi = self.inchi
        c.compartment = self.compartment
        c.chebi_id = self.chebi_id
        c.alt_chebi_ids = copy.deepcopy(self.alt_chebi_ids)
        c.kegg_id = self.kegg_id
        c.inchikey = self.inchikey
        c.position = self.position.copy()
        return c

    @classmethod
    def create_sink_compound(cls, related_compound: 'Compound') -> 'Compound':
        if related_compound.compartment.endswith(Compound.COMPARTMENT_DELIMITER + Compound.COMPARTMENT_SINK):
            raise BadRequestException("Cannot add a sink reaction to another sink reaction")

        return Compound(
            id=related_compound.id + "_s",
            name=related_compound.name,
            compartment=Compound.COMPARTMENT_SINK,
            chebi_id=related_compound.chebi_id,
            inchikey=related_compound.inchikey,
            network=related_compound.network
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
        
        flat_delim = Compound.FLATTENING_DELIMITER
        skip_list = [ cls.COMPARTMENT_EXTRACELL ]
        for compart in skip_list:
            if id.endswith(Compound.COMPARTMENT_DELIMITER + compart) or (is_compartment and id == compart):
                return id
        return slugify_id(ctx_name + flat_delim + id.replace(flat_delim,Compound.COMPARTMENT_DELIMITER))
     
    @classmethod
    def from_biota(cls, id=None, name="", biota_compound=None, chebi_id="", kegg_id="", inchikey="", compartment="", network=None) -> 'Compound':
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
            if inchikey:
                try:
                    biota_compound = BiotaCompound.get(BiotaCompound.inchikey == inchikey)
                except:
                    pass
            
            if not biota_compound and chebi_id:
                if isinstance(chebi_id, float) or isinstance(chebi_id, int):
                    chebi_id = f"CHEBI:{chebi_id}"
                if re.match(r"CHEBI\:\d+$", chebi_id): # not in chebi_id:
                    chebi_id = chebi_id
                try:
                    biota_compound = BiotaCompound.get(BiotaCompound.chebi_id == chebi_id)
                except:
                    pass
            
            if not biota_compound and kegg_id:
                try:
                    biota_compound = BiotaCompound.get(BiotaCompound.kegg_id == kegg_id)
                except:
                    pass
        
        if not biota_compound:
            raise BadRequestException(f"Cannot find compound (inchikey={inchikey}, chebi_id={chebi_id}, kegg_id={kegg_id})")

        if not compartment:
            compartment = Compound.COMPARTMENT_CYTOSOL
        if not name:
            name = biota_compound.name
        
        c = Compound(
            id=id, 
            name=name, 
            compartment=compartment, 
            network=network
        )
        c.chebi_id = biota_compound.chebi_id
        c.kegg_id = biota_compound.kegg_id
        c.inchikey = biota_compound.inchikey
        c.charge = biota_compound.charge
        c.formula = biota_compound.formula
        c.mass = biota_compound.mass
        if biota_compound.position is not None:
            c.position.x = biota_compound.position.x
            c.position.y = biota_compound.position.y
            c.position.z = biota_compound.position.z

        return c

    # -- G --

    def get_level(self):
        if self.is_major:
            return self.LEVEL_MAJOR.lower()
        elif self.is_cofactor:
            return self.LEVEL_COFACTOR.lower()
        else:
            return self.LEVEL_MINOR.lower()

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

    # -- I --
 
    @property
    def is_intracellular(self)->bool:
        """
        Test if the compound is intracellular
        
        :return: True if the compound is intracellular, False otherwise
        :rtype: `bool`
        """
        
        compartment_suffix = self.compartment.split(Compound.COMPARTMENT_DELIMITER)[-1]
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

        compartment_suffix = self.compartment.split(Compound.COMPARTMENT_DELIMITER)[-1]
        return compartment_suffix == Compound.COMPARTMENT_BIOMASS

    @property
    def is_sink(self)->bool:
        """
        Test if the compound is a sink compound
        
        :return: True if the compound is a sink compound, False otherwise
        :rtype: `bool`
        """

        compartment_suffix = self.compartment.split(Compound.COMPARTMENT_DELIMITER)[-1]
        return compartment_suffix == Compound.COMPARTMENT_SINK

    @property
    def is_steady(self)->bool:
        """
        Test if the compound is at steady state (is intracellular)
        
        :return: True if the compound is steady, False otherwise
        :rtype: `bool`
        """

        compartment_suffix = self.compartment.split(Compound.COMPARTMENT_DELIMITER)[-1]
        return self.COMPARTMENTS[compartment_suffix]["is_steady"]

    @property
    def is_cofactor(self)->bool:
        """
        Test if the compound is a factor
        
        :return: True if the compound is intracellular, False otherwise
        :rtype: `bool`
        """
        
        for pattern in self.COFACTOR_NAME_PATTERNS:
            if pattern in self.name:
                return True
        
        return self.chebi_id in self.COFACTORS

    @property
    def is_major(self)->bool:
        """
        Test if the compound is a major metabolite
        
        :return: True if the compound is intracellular, False otherwise
        :rtype: `bool`
        """
        
        for pattern in self.MAJOR_NAME_PATTERNS:
            if pattern in self.name:
                return True
        
        return self.chebi_id in self.MAJORS 
    
    @property
    def is_minor(self)->bool:
        return (not self.is_cofactor) and (not self.is_major)

    # -- M --
    
    @classmethod
    def merge_compounds(self, comps: List['Compound'], compartment=None, oligomerization=None) -> 'Compound':
        """ Merge a list of compounds (oligomerisation) """

        if compartment is None:
            compartment = comps[0].compartment

        names = []
        for comp in comps:
            names.append(comp.name)
        
        if oligomerization is not None:
            names.append(oligomerization)

        c = Compound(name=",".join(names), compartment=compartment)
        c.chebi_id = ",".join([ comp_.chebi_id or "" for comp_ in comps ])
        c.kegg_id = ",".join([ comp_.kegg_id or "" for comp_ in comps ])
        c.charge = str(sum([ float(comp_.charge or 0.0) for comp_ in comps ]))
        c.formula = ",".join([ comp_.formula or "" for comp_ in comps ])
        c.mass = str(sum([ float(comp_.mass or 0.0) for comp_ in comps ]))
        c.monoisotopic_mass = str(sum([ float(comp_.monoisotopic_mass or 0.0) for comp_ in comps ]))
        if comps[0].position is not None:
            c.position.x = comps[0].position.x
            c.position.y = comps[0].position.y
            c.position.z = comps[0].position.z

        return c
    