# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import uuid
from typing import List
from pathlib import Path

from gws.logger import Error
from gws.model import Model, Resource, ResourceSet
from gws.utils import generate_random_chars, slugify
from gws.view import DictView
from gws.json import *

from biota.compound import Compound as BiotaCompound
from biota.reaction import Reaction as BiotaReaction
from biota.enzyme import Enzyme as BiotaEnzyme
from biota.taxonomy import Taxonomy as BiotaTaxo

def slugify_id(_id):
    return slugify(_id, snakefy=True, to_lower=False)
    
flattening_delimiter = ":"

# ####################################################################
#
# Error class
#
# ####################################################################


class NoCompartmentFound(Error): 
    pass

class CompoundDuplicate(Error): 
    pass

class SubstrateDuplicate(Error): 
    pass

class ProductDuplicate(Error): 
    pass

class ReactionDuplicate(Error): 
    pass

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
    COMPARTMENT_BIOMASS    = "b"
    COMPARTMENT_EXTRACELL  = "e"
    VALID_COMPARTMENTS     = ["c","n","b","e"]
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
            
        if not compartment in self.VALID_COMPARTMENTS:
            raise Error("gena.network.Compound", "__init__", "Invalid compartment")  
        
        self.compartment = compartment   
    
        if id:
            self.id = slugify_id(id)
        else:
            # try to use chebi compound name if possible
            if not name:
                if chebi_id:
                    try:
                        c = BiotaCompound.get(BiotaCompound.chebi_id == chebi_id)
                        name = c.title
                    except:
                        name = chebi_id
                else:
                    raise Error("gena.network.Compound", "__init__", "Please provide at least a valid compound id, name or chebi_id")
                    
                
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
        
    # -- F --
    
    @classmethod
    def _flatten_id(cls, id, ctx_name, is_compartment=False) -> str:
        """
        Flattens a compound or compartment id
        
        :param id: The id
        :type id: `str`
        :param ctx_name: The name of the (metabolic, biological, network) context
        :type ctx_name: `str`
        :param is_compartment: True if it is a compartement id, Otherwise it is a compound id
        :type is_compartment: `bool`
        :return: The flattened id
        :rtype: `str`
        """
        
        delim = cls._flattening_delimiter
        skip_list = [ cls.COMPARTMENT_EXTRACELL ]
        for c in skip_list:
            if id.endswith("_" + c) or (is_compartment and id == c):
                return id

        return slugify_id(ctx_name + delim + id.replace(delim,"_"))
     
    @classmethod
    def from_biota(cls, biota_compound=None, chebi_id=None, kegg_id=None, compartment=None, network=None) -> 'Compound':
        """
        Create a network compound from a ChEBI of Kegg id
        
        :param biota_compound: The biota compound to use. If not provided, the chebi_id or keeg_id are used to fetch the corresponding compound from the biota db.
        :type biota_compound: `biota.compound.Compound`
        :param chebi_id: The ChEBI id
        :type chebi_id: `str`
        :param kegg_id: The Kegg id
        :type kegg_id: `str`
        :return: The network compound
        :rtype: `gena.network.Compound`
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
                    raise Error("gena.network.Compound", "from_biota", "Invalid arguments")
            except:
                raise Error("gena.network.Compound", "from_biota", "Chebi compound not found")
        else:
            comp = biota_compound
            
        if compartment is None:
            compartment = Compound.COMPARTMENT_CYTOSOL
            
        c = cls(name=comp.name, compartment=compartment, network=network)
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
        
        return self.compartment != self.COMPARTMENT_EXTRACELL and self.compartment != self.COMPARTMENT_BIOMASS 

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
        
# ####################################################################
#
# Reaction class
#
# ####################################################################

class Reaction:   
    """
    Class that represents a network reaction. 
    
    Network reactions are proxy of biota reaction (i.e. Rhea compounds). 
    They a used to build reconstructed digital twins. 

    :property id: The id of the reaction
    :type id: `str`
    :property name: The name of the reaction
    :type name: `str`
    :property network: The network of the reaction
    :type network: `gena.network.Network`
    :property direction: The direction of the reaction. Bidirectional (B), Left direction (L), Righ direction (R)
    :type direction: `str`
    :property lower_bound: The lower bound of the reaction flux (metabolic flux)
    :type lower_bound: `float`
    :property upper_bound: The upper bound of the reaction flux (metabolic flux)
    :type upper_bound: `float`
    :property rhea_id: The corresponding Rhea if of the reaction
    :type rhea_id: `str`
    :property enzyme: The details on the enzyme that regulates the reaction
    :type enzyme: `dict`
    """
    
    id: str = None
    name: str = None
    network: 'Network' = None
    direction: str = "B"
    lower_bound: float = -1000.0
    upper_bound: float = 1000.0
    rhea_id: str = None
    enzyme: dict = None
    
    _tax_ids = []
    _substrates: dict = None
    _products: dict = None
    _flattening_delimiter = flattening_delimiter
    
    def __init__(self, id: str="", name: str = "", network: 'Network' = None, \
                 direction: str= "B", lower_bound: float = -1000.0, upper_bound: float = 1000.0, \
                 enzyme: dict={}, rhea_id=""):  
        
        if id:
            self.id = slugify_id(id)
        else:
            self.id = slugify_id(name)
        
        self.name = name
        self.enzyme = enzyme
        
        if not self.id:
            if self.enzyme:
                self.id = self.enzyme.get("ec_number","")
                self.name = self.id
        
        if not self.id:
            raise Error("gena.network.Reaction", "__init__", "At least a valid reaction id or name is reaction")
            
        if direction in ["B", "L", "R"]:
            self.direction = direction
            
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self._substrates = {}
        self._products = {}
        
        if network:
            self.add_to_network(network)
        
        self.rhea_id = rhea_id
        
    # -- A --

    def add_to_network(self, net: 'Network'):  
        """
        Adds the reaction to a newtork
        
        :param net: The network
        :type net: `gena.network.Network`
        """
        
        net.add_reaction(self)
    
    def add_substrate( self, comp: Compound, stoich: float ):
        """
        Adds a substrate to the reaction
        
        :param comp: The compound to add as substrate
        :type comp: `gena.network.Compound`
        :param stoich: The stoichiometry of the compound in the reaction
        :type stoich: `int`
        """
        
        if comp.id in self._substrates:
            raise SubstrateDuplicate("gena.network.Reaction", "add_substrate", f"Substrate duplicate (id= {comp.id})")
        
        # add the compound to the reaction network
        if self.network:
            if not comp.id in self.network.compounds:
                self.network.add_compound(comp)

        self._substrates[comp.id] = {
            "compound": comp,
            "stoichiometry": abs(float(stoich))
        }
    
    def add_product( self, comp: Compound, stoich: float ):
        """
        Adds a product to the reaction
        
        :param comp: The compound to add as product
        :type comp: `gena.network.Compound`
        :param stoich: The stoichiometry of the compound in the reaction
        :type stoich: `int`
        """
        
        if comp.id in self._products:
            raise ProductDuplicate("gena.network.Reaction", "add_substrate", "Product duplicate (id= {comp.id})")
        
        # add the compound to the reaction network
        if self.network:
            if not comp.id in self.network.compounds:
                self.network.add_compound(comp)
                
        self._products[comp.id] = {
            "compound": comp,
            "stoichiometry": abs(float(stoich))
        }

    # -- F --
    
    @classmethod
    def _flatten_id(cls, id:str , ctx_name:str) -> str:
        """
        Flattens a reaction id
        
        :param id: The id
        :type id: `str`
        :param ctx_name: The name of the (metabolic, biological, network) context
        :type ctx_name: `str`
        :return: The flattened id
        :rtype: `str`
        """
        
        delim = cls._flattening_delimiter
        return slugify_id(ctx_name + delim + id.replace(delim,"_"))
        
    @classmethod
    def from_biota(cls, biota_reaction=None, rhea_id=None, ec_number=None, tax_id=None, tax_search_method='bottom_up', network=None) -> 'Reaction':
        """
        Create a biota reaction from a Rhea id or an EC number.
        
        :param biota_reaction: The biota reaction to use. If not provided, the rhea_id or ec_number are used to fetch the corresponding reaction from the biota db.
        :type biota_reaction: `biota.compound.Compound`
        :param rhea_id: The Rhea id of the reaction. If given, the other parameters are not considered
        :rtype rhea_id: `str`
        :param ec_number: The EC number of the enzyme related to the reaction. If given, all the Rhea reactions associated with this enzyme are retrieved for the biota DB
        :rtype ec_number: `str`
        :param tax_id: The taxonomy ID of the target organism. If given, the enzymes are fetched in the corresponding taxonomy. If the taxonomy ID is not valid, no reaction is built.  
        :rtype tax_id: `str`
        :param tax_search_method: The taxonomy search method (Defaults to `bottom_up`). 
            * `none`: the algorithm will only search at the given taxonomy level
            * `bottom_up`: the algorithm will to traverse the taxonomy tree to search in the higher taxonomy levels until a reaction is found
        :rtype tax_search_method: `none` or `bottom_up`
        :param network: The network to which the reaction is added. If the reaction already exists, an exception is raised.
        :return: The network reaction
        :rtype: `gena.network.Reaction`
        """
        
        rxns = []
        #tax_tree = BiotaTaxo._tax_tree
        
        all_tax = {}
        def __create_rxn(rhea_rxn, network, enzyme):
            if enzyme:
                
                e = {
                    "title": enzyme.title,
                    "ec_number": enzyme.ec_number,
                }
                
                e["tax"] = {}
                try:
                    tax = BiotaTaxo.get(BiotaTaxo.tax_id == enzyme.tax_id)
                except:
                    tax = None
                    
                if tax:
                    e["tax"][tax.rank] = {
                        "tax_id": tax.tax_id,
                        "title": tax.title
                    }
                    
                    for t in tax.ancestors:
                        e["tax"][t.rank] = {
                            "tax_id": t.tax_id,
                            "title": t.title
                        }
                    
                #for f in BiotaTaxo._tax_tree: 
                #    e[f] = getattr(enzyme, "tax_"+f)
                    
                if enzyme.related_deprecated_enzyme:
                    e["related_deprecated_enzyme"] = {
                        "ec_number": enzyme.related_deprecated_enzyme.ec_number,
                        "reason": enzyme.related_deprecated_enzyme.data["reason"],
                    }
                
                pwy = enzyme.pathway
                if pwy:
                    e["pathway"] = pwy.data
                    
            else:
                e = {}
                
            rxn = cls(name=rhea_rxn.rhea_id+"_"+enzyme.ec_number, 
                      network=network, 
                      direction=rhea_rxn.direction,
                      enzyme=e)
      
            eqn = rhea_rxn.data["equation"]
            for chebi_id in eqn["substrates"]:
                stoich =  eqn["substrates"][chebi_id]
                biota_comp = BiotaCompound.get(BiotaCompound.chebi_id == chebi_id)
                c = Compound(name=biota_comp.name, compartment=Compound.COMPARTMENT_CYTOSOL)
                c.chebi_id = biota_comp.chebi_id
                c.kegg_id = biota_comp.kegg_id
                c.charge = biota_comp.charge
                c.formula = biota_comp.formula
                c.mass = biota_comp.mass
                c.monoisotopic_mass = biota_comp.monoisotopic_mass
                rxn.add_substrate(c, stoich)

            for chebi_id in eqn["products"]:
                stoich = eqn["products"][chebi_id]
                biota_comp = BiotaCompound.get(BiotaCompound.chebi_id == chebi_id)
                c = Compound(name=biota_comp.name, compartment=Compound.COMPARTMENT_CYTOSOL)
                c.chebi_id = biota_comp.chebi_id
                c.kegg_id = biota_comp.kegg_id
                c.charge = biota_comp.charge
                c.formula = biota_comp.formula
                c.mass = biota_comp.mass
                c.monoisotopic_mass = biota_comp.monoisotopic_mass
                rxn.add_product(c, stoich)
            
            return rxn
        
        if biota_reaction:
            rhea_rxn = biota_reaction
            _added_rxns = []
            for e in rhea_rxn.enzymes:
                if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                    continue
                _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)

                try:
                    rxns.append( __create_rxn(rhea_rxn, network, e) )
                except:
                    pass
            return rxns
        
        elif rhea_id:
            tax = None
            Q = BiotaReaction.select().where(BiotaReaction.rhea_id == rhea_id)
            
            if not Q:
                raise Error("gena.network.Reaction", "from_biota", f"No reaction found with rhea id {rhea_id}")
          
            _added_rxns = []
            for rhea_rxn in Q:
                for e in rhea_rxn.enzymes:
                    if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                        continue
                    _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                    
                    try:
                        rxns.append( __create_rxn(rhea_rxn, network, e) )
                    except:
                        pass
                 
            return rxns
            
        elif ec_number:
            tax = None
            e = None
            
            if tax_id:
                try:
                    tax = BiotaTaxo.get(BiotaTaxo.tax_id == tax_id)
                except:
                    raise Error("Reaction", "from_biota", f"No taxonomy found with tax_id {tax_id}") 

                Q = BiotaEnzyme.select_and_follow_if_deprecated(ec_number = ec_number, tax_id = tax_id)
                if not Q:
                    if tax_search_method == 'bottom_up':
                        found_Q = []
                        Q = BiotaEnzyme.select_and_follow_if_deprecated(ec_number = ec_number)

                        #-> for each ec: we select the best enzyme
                        #is_best_enzyme_found_for_this_ec = False
                        #for e in Q:
                        #    for t in tax.ancestors:
                        #        if t.rank == "no rank":
                        #            continue
                        #        if getattr(e, "tax_"+t.rank) == t.tax_id:
                        #            found_Q.append(e)
                        #            is_best_enzyme_found_for_this_ec = True
                        #            break  #-> stop at this taxonomy rank
                        
                        tab = {}
                        for e in Q:
                            if not e.ec_number in tab:
                                tab[e.ec_number] = []
                                
                            tab[e.ec_number].append(e)
                        
                        for t in tax.ancestors:
                            is_found = False
                            for ec in tab:
                                e_group = tab[ec]
                                for e in e_group:
                                    if t.rank == "no rank":
                                        continue
                                    if getattr(e, "tax_"+t.rank) == t.tax_id:
                                        found_Q.append(e)
                                        is_found = True
                                        break  #-> stop at this taxonomy rank
                                
                                if is_found:
                                    del tab[ec]
                                    break
                        
                        # add remaining enzyme
                        for ec in tab:
                            e_group = tab[ec]
                            for e in e_group:
                                found_Q.append(e)
                                break
                                   
                                
                        if found_Q:
                            Q = found_Q
                
                if not Q:
                    raise Error("gena.network.Reaction", "from_biota", f"No enzyme found with ec number {ec_number}")
                    
                _added_rxns = []
                messages = []
                for e in Q:
                    if not e.reactions:
                        messages.append(f"No rhea found for {e.ec_number}")
                                        
                    for rhea_rxn in e.reactions:
                        if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                            continue
                        _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                        
                        try:
                            rxns.append( __create_rxn(rhea_rxn, network, e) )
                        except:
                            # reaction duplicate
                            # skip error!
                            pass
                        
                
                if not rxns:
                    messages.append(f"No new reactions found with ec number {ec_number}")
                    raise Error("gena.network.Reaction", "from_biota", ", ".join(messages))
                    
            else:
                #Q = BiotaEnzyme.select().where(BiotaEnzyme.ec_number == ec_number)
                Q = BiotaEnzyme.select_and_follow_if_deprecated(ec_number = ec_number)
                
                if not Q:
                    raise Error("gena.network.Reaction", "from_biota", f"No enzyme found with ec number {ec_number}")
                
                _added_rxns = []
                messages = []
                for e in Q:
                    if not e.reactions:
                        messages.append(f"No rhea found for {e.ec_number}")
                        
                    for rhea_rxn in e.reactions:
                        if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                            continue
                        _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                        
                        try:
                            rxns.append( __create_rxn(rhea_rxn, network, e) ) 
                        except:
                            pass
                        
                if not rxns:
                    messages.append(f"No new reactions found with ec number {ec_number}")
                    raise Error("gena.network.Reaction", "from_biota",  ", ".join(messages))
        else:
            raise Error("gena.network.Reaction", "from_biota", "Invalid arguments")

        return rxns

    # -- I --
    
    @property
    def is_empty(self):
        return not bool(self._substrates) and not bool(self._products)
        
    # -- P --
    
    @property
    def products(self) -> str:
        """
        Returns the products of the reaction
        
        :return: The list of products as {key,value} dictionnary
        :rtype: `dict`
        """
        
        return self._products
    
    # -- R --
    
    def get_related_biota_reaction(self):
        """
        Get the biota reaction that is related to this network reaction
        
        :return: The biota compound corresponding to the rhea id. Returns `None` is no biota reaction is found
        :rtype: `bioa.reaction.Reaction`, `None`
        """
        
        try:
            return BiotaReaction.get(BiotaReaction.rhea_id == self.rhea_id)
        except:
            return None
    
    # -- S --
    
    @property
    def substrates(self) -> dict:
        """
        Returns the substrates of the reaction
        
        :return: The list of substrates as {key,value} dictionnary
        :rtype: `dict`
        """
        
        return self._substrates
    
    # -- T --
    
    def to_str(self, only_ids=False) -> str:
        """
        Returns a string representation of the reaction
        
        :return: The string
        :rtype: `str`
        """
        
        _left = []
        _right = []
        _dir = {"L": " <==(E)== ", "R": " ==(E)==> ", "B": " <==(E)==> "}
        
        for k in self._substrates:
            sub = self._substrates[k]
            comp = sub["compound"]
            stoich = sub["stoichiometry"]
            if only_ids:
                _id = comp.chebi_id if comp.chebi_id else comp.id
                _left.append( f"({stoich}) {_id}" )
            else:
                _left.append( f"({stoich}) {comp.id}" )
        
        for k in self._products:
            sub = self._products[k]
            comp = sub["compound"]
            stoich = sub["stoichiometry"]
            if only_ids:
                _id = comp.chebi_id if comp.chebi_id else comp.id
                _right.append( f"({stoich}) {_id}" )
            else:
                _right.append( f"({stoich}) {comp.id}" )
        
        if not _left:
            _left = ["*"]
            
        if not _right:
            _right = ["*"]
            
        _str = " + ".join(_left) + _dir[self.direction].replace("E", self.enzyme.get("ec_number","")) + " + ".join(_right)
        #_str = _str + " " + str(self.enzyme)
        return _str
    
# ####################################################################
#
# Network class
#
# ####################################################################

class Network(Resource):
    """
    Class that represents a network. 
    
    A network is a collection of reconstructed metabolic pathways.
    """
    
    _compounds = None
    _reactions = None
    _compartments = None
    _medium = None
    
    _fts_fields = {'title': 2.0, 'description': 1.0}
    #_table_name = "gena_network"
    
    _flattening_delimiter = flattening_delimiter
    _defaultNetwork = None
    _stats = None
    _cofactor_freq_threshold = 0.7
    
    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )

        self._compounds = {}
        self._reactions = {}
        self._compartments = {
            "e": "extracellular",
            "c": "cytosol",
            "n": "nucleus",
            "b": "biomass"
        }
        self._medium = {}
        
        if self.data:
            self.__build_from_dump(self.data["network"])
        else:
            self.data = {
                'title': 'Network',
                'description': '',
                'network': None,
                "tags":{
                    "reactions": {},
                    "compounds": {}
                },
            }
        
        self._stats = {}
        
        # only used for the reconstruction
        # self.data["errors"] = []
        
    # -- A --
        
    def add_compound(self, comp: Compound):
        """
        Adds a compound 
        
        :param comp: The compound to add
        :type comp: `gena.network.Compound`
        """
        
        if not isinstance(comp, Compound):
            raise Error("Network", "add_compound", "The compound must an instance of Compound")
        
        if comp.network and comp.network != self:
            raise Error("Network", "add_compound", "The compound is already in another network")
        
        if comp.id in self._compounds:
            raise CompoundDuplicate("Network", "add_compound", f"Compound id {comp.id} duplicate")
        
        if not comp.compartment:
            raise NoCompartmentFound("Network", "add_compound", "No compartment defined for the compound")
        
        if not comp.compartment in self._compartments:
            self.compartment[comp.compartment] = comp.compartment
        
        comp.network = self
        self.compounds[comp.id] = comp
        self._stats = {}
        
    def add_reaction(self, rxn: Reaction):
        """
        Adds a product
        
        :param rxn: The reaction to add
        :type rxn: `gena.network.Reaction`
        """
        
        if not isinstance(rxn, Reaction):
            raise Error("Network", "add_reaction", "The reaction must an instance of Reaction")
        
        if rxn.network:
            raise Error("Network", "add_reaction", "The reaction is already in a network")
        
        if rxn.id in self.reactions:
            raise ReactionDuplicate("Network", "add_reaction", f"Reaction id {rxn.id} duplicate")
        
        # add reaction compounds to the network
        for k in rxn.substrates:            
            sub = rxn.substrates[k]
            comp = sub["compound"]
            if not comp.id in self.compounds:
                self.add_compound(comp)
        
        for k in rxn.products:
            prod = rxn.products[k]
            comp = prod["compound"]
            if not comp.id in self.compounds:
                self.add_compound(comp)
                
        # add the reaction
        rxn.network = self
        self.reactions[rxn.id] = rxn
        self._stats = {}
              
    # -- B --
    
    def __build_from_dump(self, data):
        """
        Create a network from a dump
        """
        
        if not data.get("compartments"):
            raise Error("Network", "__build_from_dump", f"Invalid network dump")
            
        delim = self._flattening_delimiter
        self.compartments = data["compartments"]
        ckey = "compounds" if "compounds" in data else "metabolites"
        
        added_comps = {}
        for val in data[ckey]:
            compart = val["compartment"]
            
            if not compart in self.compartments:
                raise Error("Network", "__build_from_dump", f"The compartment '{compart}' of the compound '{val['id']}' not declared in the lists of compartments")
            
            chebi_id = ""
            comp = None

            id = val["id"]
            chebi_id = val.get("chebi_id","")
            if "CHEBI:" in id:
                chebi_id = id
            
            if chebi_id:
                try:
                    comp = Compound.from_biota(chebi_id=chebi_id, )
                except:
                    pass
                 
            if not comp:   
                comp = Compound(
                    id=val["id"].replace(delim,"_"), \
                    name=val["name"], \
                    network=self, \
                    compartment=compart,\
                    charge = val.get("charge",""),\
                    mass = val.get("mass",""),\
                    monoisotopic_mass = val.get("monoisotopic_mass",""),\
                    formula = val.get("formula",""),\
                    inchi = val.get("inchi",""),\
                    chebi_id = val.get("chebi_id",""),\
                    kegg_id = val.get("kegg_id","")\
                )
            
            added_comps[id] = comp
            
        for val in data["reactions"]:
            rxn = Reaction(
                id=val["id"].replace(delim,"_"), \
                name=val.get("name"), \
                network=self, \
                lower_bound=val.get("lower_bound", Reaction.lower_bound), \
                upper_bound=val.get("upper_bound", Reaction.upper_bound), \
                enzyme=val.get("enzyme",{}),\
                direction=val.get("direction","B"),\
                rhea_id=val.get("rhea_id","")\
            )
            
            for comp_id in val[ckey]:
                comp = added_comps[comp_id]
                
                # search according to compound ids
                if "CHEBI:" in comp_id:
                    comps = self.get_compounds_by_chebi_id(comp_id)
                    # select the compound in the good compartment
                    for c in comps:
                        if c.compartement == comp.compartement:
                            break
                             
                stoich = val[ckey][comp_id]
                if stoich < 0:
                    rxn.add_substrate( comp, stoich )
                elif stoich > 0:
                    rxn.add_product( comp, stoich )
        
        self.data["name"] = data.get("name","Network").replace(delim,"_")
        self.data["description"] = data.get("description","")
        
        if data.get("tags"):
            self.data["tags"] = data.get("tags")
        
    # -- C --
    
    def copy(self) -> 'Network':
        return Network.from_json( self.to_json()["data"]["network"] )
        
    @property
    def compartments(self):
        """
        Returns the list of compartments
        
        :rtype: `dict`
        """
        return self._compartments
    
    @compartments.setter
    def compartments(self, vals: list):
        """ 
        Set the list of compartments.
        
        :param vals: The list of compartments
        :type vals: `list` of `str`
        """
        self._compartments = vals
    
    @property
    def compounds(self) -> dict:
        """
        Returns the list of compounds
        
        :rtype: `dict`
        """
        
        return self._compounds
    
    # -- D --

    @property
    def description(self) -> str:
        """ 
        Set the description.
        
        :param description: The description
        :type description: `str`
        """
        
        return self.data.get("description")
    
    @description.setter
    def description(self, desc:str ):
        """ 
        Set the description of the compartment
        
        :return: The description
        :rtype: `str`
        """
        
        self.data["description"] = ""
    
    def dumps(self, stringify=False, prettify=False):
        """
        Dumps the network
        """
        
        _met_json = []
        _rxn_json = []
        
        for _met in self.compounds.values():
            _met_json.append({
                "id": _met.id,
                "name": _met.name,
                "charge": _met.charge,
                "mass": _met.mass,
                "monoisotopic_mass": _met.monoisotopic_mass,
                "formula": _met.formula,
                "inchi": _met.inchi,
                "compartment": _met.compartment,
                "chebi_id": _met.chebi_id,
                "kegg_id": _met.kegg_id
            })
            
        for _rxn in self.reactions.values():
            _rxn_met = {}
            for sub in _rxn.substrates.values():
                _rxn_met.update({
                    sub["compound"].id: -abs(sub["stoichiometry"])
                })
                
            for prod in _rxn.products.values():
                _rxn_met.update({
                    prod["compound"].id: abs(prod["stoichiometry"])
                })
            
            _rxn_json.append({
                "id": _rxn.id,
                "name": _rxn.name,
                "enzyme": _rxn.enzyme,
                "rhea_id": _rxn.rhea_id,
                "metabolites": _rxn_met,
            })
  
        _json = {
            "metabolites": _met_json,
            "reactions": _rxn_json,
            "compartments": self.compartments,
            "tags": self.data["tags"]
        }
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
       
    # -- E --
    
    def exists(self, elt: (Compound, Reaction))->bool:
        """
        Check that a compound or a reaction exists in the the network
        
        :param elt: The element (compound or reaction)
        :type elt: `gws.gena.Compound` or `gws.gena.Reaction`
        :return: True if the element exists, False otherwise
        :rtype: `bool`
        """
        
        if isinstance(elt, Reaction):
            return elt.id in self.reactions
        
        if isinstance(elt, Compound):
            return elt.id in self.compounds
            
        raise Error("Network", "exists", "Invalid element. The element must be an instance of gws.gena.Compound or gws.gena.Reaction")
    
    # -- E --
    
    def _export(self, file_path: str, file_format:str = None):
        """ 
        Export the network to a repository

        :param file_path: The destination file path
        :type file_path: str
        """
        
        file_extension = Path(file_path).suffix
        
        with open(file_path, 'r') as fp:
            if file_extension in [".json"] or file_format == ".json":
                data = self.to_json()
                json.dump(data, fp)
            elif file_extension in [".csv", ".txt", ".tsv"] or file_format in [".csv", ".txt", ".tsv"]:
                fp.write(self.to_csv())
            else:
                raise Error("Network","_export","Invalid file format")
            
    # -- F --
    
    @classmethod
    def from_json(cls, data: dict) -> 'Network':
        """
        Create a network from a JSON dump
        
        :param data: The dictionnay describing the network
        :type data: `dict`
        :return: The network
        :rtype: `gena.network.Network`
        """
        
        net = Network()
        net.__build_from_dump(data)
        net.data["network"] = net.dumps()
        return net
    
    # -- G --
    
    def get_compound_tag(self, comp_id: str, tag_name: str = None):
        """
        Get a compound tag value a compound id and a tag name.
        
        :param comp_id: The compound id
        :type comp_id: `str`
        :param tag_name: The tag name
        :type tag_name: `str`
        :return: The tag value
        :rtype: `str`
        """
        
        if tag_name:
            return self.data["tags"]["compounds"].get(comp_id,{}).get(tag_name)
        else:
            return self.data["tags"]["compounds"].get(comp_id,{})
        
    def get_compound_tags(self) -> dict:
        """
        Get all the compound tags
        
        :return: The tags
        :rtype: `dict`
        """
        
        return self.data["tags"]["compounds"]
    
    def get_reaction_tag(self, rxn_id: str, tag_name: str = None):
        """
        Get a reaction tag value a compound id and a tag name.
        
        :param rxn_id: The reaction id
        :type rxn_id: `str`
        :param tag_name: The tag name
        :type tag_name: `str`
        :return: The tags
        :rtype: `dict`
        """
        
        if tag_name:
            return self.data["tags"]["reactions"].get(rxn_id,{}).get(tag_name)
        else:
            return self.data["tags"]["reactions"].get(rxn_id,{})
        
        
    def get_reaction_tags(self) -> dict:
        """
        Get all the reaction tags
        
        :return: The tags
        :rtype: `dict`
        """
        
        return self.data["tags"]["reactions"]
    
    def get_compound_by_id(self, comp_id: str) -> Compound:
        """
        Get a compound by its id.
        
        :param comp_id: The compound id
        :type comp_id: `str`
        :return: The compound or `None` if the compond is not found
        :rtype: `gena.network.Compound` or `None`
        """
        
        return self._compounds.get(comp_id)
    
    def get_compounds_by_chebi_id(self, chebi_id: str, compartment: str=None)->Compound:
        """
        Get a compound by its chebi id and compartment.
        
        :param chebi_id: The chebi id of the compound
        :type chebi_id: `str`
        :param compartment: The compartment of the compound
        :type compartment: `str`
        :return: The compound or `None` if the compond is not found
        :rtype: `gena.network.Compound` or `None`
        """
        
        if isinstance(chebi_id, float) or isinstance(chebi_id, int):
            chebi_id = f"CHEBI:{chebi_id}"
        
        if "CHEBI" not in chebi_id:
            chebi_id = f"CHEBI:{chebi_id}"
        
        _list = []
        for chebi_id in self._compounds:
            comp = self._compounds[chebi_id]
            if comp.chebi_id == chebi_id:
                if compartment is None:
                    _list.append(comp)
                elif comp.compartment == compartment:
                    _list.append(comp)
        
        return _list
    
    def get_reaction_by_id(self, rxn_id: str)->Reaction:
        """
        Get a reaction by its id.
        
        :param rxn_id: The reaction id
        :type rxn_id: `str`
        :return: The reaction or `None` if the reaction is not found
        :rtype: `gena.network.Reaction` or `None`
        """
        
        return self._reactions.get(rxn_id)
    
    def get_reaction_by_ec_number(self, ec_number: str)->Reaction:
        """
        Get a reaction by its ec number.
        
        :param ec_number: The ec number of the reaction
        :type ec_number: `str`
        :return: The reaction or `None` if the reaction is not found
        :rtype: `gena.network.Reaction` or `None`
        """
        
        for k in self._reactions:
            rxn = self._reactions[k]
            if rxn.ec_number == ec_number:
                return rxn

    def _get_gap_info(self)->dict:
        """
        Get gap information
        """
        
        _info = {}
        for k in self._compounds:
            _info[k] = {
                "is_substrate": False,
                "is_product": False,
                "is_gap": False
            }
            
        for k in self._reactions:
            rxn = self._reactions[k]
            for c_id in rxn._substrates:
                comp = rxn._substrates[c_id]["compound"]
                _info[comp.id]["is_substrate"] = True
                
            for c_id in rxn._products:
                comp = rxn._products[c_id]["compound"]
                _info[comp.id]["is_product"] = True
        
        for k in _info:
            if not _info[k]["is_product"] or not _info[k]["is_substrate"]:
                comp = self._compounds[k]
                if comp.is_intracellular:
                    _info[k]["is_gap"] = True
                    
        return _info
    
    def get_biomass_reaction(self) -> Reaction:
        """ 
        Get the biomass reaction if it exists
        
        :returns: The biomass reaction (or `None` if the biomass reaction does not exist)
        :rtype: `gena.network.Reaction` or `None`
        """
        
        for k in self.reactions:
            if "biomass" in k.lower():
                return self.reactions[k]
            
        return None
    
    # -- I --

    @classmethod
    def _import(cls, file_path: str, file_format:str = None) -> 'Network':
        """ 
        Import a network from a repository
        
        :param file_path: The source file path
        :type file_path: str
        :returns: the parsed data
        :rtype: any
        """

        file_extension = Path(file_path).suffix
        
        if file_extension in [".json"] or file_format == ".json":
            with open(file_path, 'r') as fp:
                try:
                    _json = json.load(fp)
                except Exception as err:
                    raise Error("Network","_import", f"Cannot load JSON file {file_path}. Error: {err}")
                    
                if _json.get("reactions"):
                    # is a raw network data
                    net = cls.from_json(_json)
                elif _json.get("data",{}).get("network"): 
                    # is gws resource
                    net = cls.from_json(_json["data"]["network"])
                else:
                    raise Error("Network","_import","Invalid network data")
        
        else:
            raise Error("Network","_import","Invalid file format")
            
        return net
    
    # -- N --
    
    @property
    def name(self):
        """ 
        Get the name of the compartment
        
        Alias of :meth:`get_title` 
        :return: The name
        :rtype: `str`
        """
        
        return self.get_title()
    
    @name.setter
    def name(self, name:str):
        """ 
        Set the name of the compartment.
        
        Alias of :meth:`set_title` 
        :param name: The name
        :type name: `str`
        """
        
        return self.set_title(name)
    
    # -- P --
    
    # -- R --
    
    @property
    def reactions(self) -> dict:
        """
        Returns the list of reactions
        
        :rtype: `dict`
        """
        
        return self._reactions #self.kv_store["reactions"]
    
    def remove_reaction(self, rxn_id: str):
        """
        Remove a reaction from the network
        
        :param rxn_id: The id of the reaction to remove
        :type rxn_id: `str`
        """
        
        del self.reactions[rxn_id]
        
    # -- S --
    
    @property
    def stats(self) -> dict:
        if self._stats:
            return self._stats
        
        stats = {
            "compound_count": len(self.compounds),
            "reaction_count": len(self.reactions),
            "compounds": {},
            "reactions": {}
        }
        
        for comp_id in self.compounds:
            stats["compounds"][comp_id] = {
                "count": 0
            }
            
        for rxn_id in self.reactions:
            rxn = self.reactions[rxn_id]
            for comp_id in rxn.products:
                stats["compounds"][comp_id]["count"] += 1
            
            for comp_id in rxn.substrates:
                stats["compounds"][comp_id]["count"] += 1
        
        if stats["compound_count"]:
            for comp_id in self.compounds:
                stats["compounds"][comp_id]["freq"] = stats["compounds"][comp_id]["count"] / stats["compound_count"]
        
        self._stats = stats
        return stats
  
    def save(self, *args, **kwargs):
        """
        Save the metwork
        """
        
        self.data["network"] = self.dumps()
        return super().save(*args, **kwargs)
    
    
    def set_reaction_tag(self, tag_id, tag: dict):
        if not isinstance(tag, dict):
            raise Error("Network", "add_tag", "The tag must be a dictionary")
            
        if not tag_id in self.data["tags"]["reactions"]:
            self.data["tags"]["reactions"][tag_id] = {}

        self.data["tags"]["reactions"][tag_id].update(tag)

    def set_compound_tag(self, tag_id, tag: dict):
        if not isinstance(tag, dict):
            raise Error("Network", "add_tag", "The tag must be a dictionary")
            
        if not tag_id in self.data["tags"]["compounds"]:
            self.data["tags"]["compounds"][tag_id] = {}

        self.data["tags"]["compounds"][tag_id].update(tag)
        
    # -- T --
    
    def to_json(self, stringify=False, prettify=False, **kwargs) -> (dict, str,):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :param kwargs: Theses parameters are passed to the super class
        :type kwargs: keyword arguments
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(**kwargs)
        _json["data"]["network"] = self.dumps() #override to account for new updates
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
    
    def to_str(self) -> str:
        """
        Returns a string representation of the network
        
        :rtype: `str`
        """
        
        _str = ""
        for _id in self.reactions:
            _str += "\n" + self.reactions[_id].to_str()
        return _str
    
    def to_csv(self) -> str:
        """
        Returns a CSV representation of the network
        
        :rtype: `str`
        """
        
        return self.to_table(stringify=True)
        
    def to_table(self, stringify=False) -> ('pandas.DataFrame', str):
        """
        Returns a tabular representation of the network
        
        :param stringify: True to stringify the table (as CSV string will be returned). False otherwise
        :type stringify: `bool`
        :rtype: `pandas.DataFrame`, `str`
        """
        
        column_names = [
            "id", "equation_str", \
            "enzyme", "ec_number", \
            "enzyme_class", \
            "is_from_gap_filling",
            "comments", \
            "substrates", "products", \
            *BiotaTaxo._tax_tree, \
            "brenda_pathway", "kegg_pathway", "metacyc_pathway"
        ]
        
        table = []
        rxn_count = 1
        for k in self.reactions:
            rxn = self.reactions[k]
            
            enz = ""
            ec = ""
            comment = []
            enzyme_class = ""
            is_from_gap_filling = False
            pathway_cols = ["", "", ""]
            tax_cols = [""] * len(BiotaTaxo._tax_tree)
            
            flag = self.get_reaction_tag(rxn.id, "is_from_gap_filling")
            if flag:
                is_from_gap_filling = True
                
            if rxn.enzyme:
                enz = rxn.enzyme.get("title","--") 
                ec = rxn.enzyme.get("ec_number","--")
                
                deprecated_enz = rxn.enzyme.get("related_deprecated_enzyme")
                if deprecated_enz:
                     comment.append(deprecated_enz["ec_number"] + " (" + deprecated_enz["reason"] + ")")

                if rxn.enzyme.get("pathway"):
                    pathway_cols = []
                    bkms = ['brenda', 'kegg', 'metacyc']
                    pw = rxn.enzyme.get("pathway")
                    if pw:
                        for db in bkms:
                            if pw.get(db):
                                pathway_cols.append( pw[db]["name"] + " (" + (pw[db]["id"] if pw[db]["id"] else "--") + ")" )
                            else:
                                pathway_cols.append("")
                            
                if rxn.enzyme.get("tax"):
                    tax_cols = []
                    tax = rxn.enzyme.get("tax")
                    for f in BiotaTaxo._tax_tree: 
                        if f in tax:
                            tax_cols.append( tax[f]["title"] + " (" + str(tax[f]["tax_id"]) + ")" )
                        else:
                            tax_cols.append("")
                
                if rxn.enzyme.get("ec_number"):
                    try:
                        enzyme_class = EnsymeClass.get(EnsymeClass.ec_numbner == rxn.enzyme.get("ec_number"))
                    except:
                        pass
                
            subs = []
            for m in rxn.substrates:
                c = rxn.substrates[m]["compound"]
                subs.append( c.name + " (" + c.chebi_id + ")" )
                
            prods = []
            for m in rxn.products:
                c = rxn.products[m]["compound"]
                prods.append( c.name + " (" + c.chebi_id + ")" )
            
            if not subs:
                subs = ["*"]
            
            if not prods:
                prods = ["*"]
            
            rxn_row = [
                rxn.id, \
                rxn.to_str(), \
                enz, ec, \
                enzyme_class, \
                is_from_gap_filling, \
                "; ".join(comment), \
                "; ".join(subs), \
                "; ".join(prods), \
                *tax_cols, \
                *pathway_cols
            ]
            
            rxn_count += 1
            table.append(rxn_row)
        
        # add the errored ec numbers
        from biota.enzyme import EnzymeClass
        
        tags = self.get_reaction_tags()
        #errors = self.data.get("logs",{}).get("reactions")
        #tags = self.get_reaction_tag()
        
        for k in tags:
            t = tags[k]
            ec = t.get("ec_number")
            is_partial_ec_number = t.get("is_partial_ec_number")
            error = t.get("error")
            if not ec:
                continue
            
            rxn_row = [""] * len(column_names)
            rxn_row[3] = ec      # ec number
            rxn_row[6] = error   # comment
            
            if is_partial_ec_number:
                try:
                    enzyme_class = EnzymeClass.get(EnzymeClass.ec_number == ec)
                    rxn_row[4] = enzyme_class.title
                except:
                    pass
            
            rxn_count += 1
            table.append(rxn_row)
            
        # export
        import pandas
        table = pandas.DataFrame(table, columns=column_names)
        table = table.sort_values(by=['ec_number'])
        if stringify:
            return table.to_csv()
        else:
            return table
        
    # -- V --
    
    def view__compound_stats__as_json(self, stringify=False, prettify=False, **kwargs) -> (dict, str,):
        return self.stats["compounds"]
    
    def view__compound_stats__as_table(self, stringify=False, **kwargs) -> (str, "DataFrame",):
        _dict = self.stats["compounds"]
        for comp_id in _dict:
            _dict[comp_id]["chebi_id"] = self._compounds[comp_id].chebi_id
        table = DictView.to_table(_dict, columns=["count", "freq", "chebi_id"], stringify=False)
        table = table.sort_values(by=['freq'], ascending=False)
        if stringify:
            return table.to_csv()
        else:
            return table
    
    def view__gaps__as_json(self, stringify=False, **kwargs) -> (str, "DataFrame",):
        return self._get_gap_info()
    
    def view__gaps__as_table(self, stringify=False, **kwargs) -> (str, "DataFrame",):
        _dict = self._get_gap_info()
        table = DictView.to_table(_dict, columns=["is_substrate", "is_product", "is_gap"], stringify=False)
        if stringify:
            return table.to_csv()
        else:
            return table

    def view__stats__as_json(self, stringify=False, prettify=False, **kwargs) -> (dict, str,):
        stats = self.stats
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
    

# ####################################################################
#
# Importer class
#
# ####################################################################
    
class NetworkImporter(JSONImporter):
    input_specs = {'file' : File}
    output_specs = {'data': Network}
    config_specs = {
        'file_format': {"type": str, "default": ".json", 'description': "File format"}
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

class NetworkExporter(JSONExporter):
    input_specs = {'data': Network}
    output_specs = {'file' : File}
    config_specs = {
        'file_name': {"type": str, "default": 'network.json', 'description': "Destination file name in the store"},
        'file_format': {"type": str, "default": ".json", 'description': "File format"},
    }
    
# ####################################################################
#
# Loader class
#
# ####################################################################

class NetworkLoader(JSONLoader):
    input_specs = {}
    output_specs = {'data' : Network}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Location of the file to import"},
        'file_format': {"type": str, "default": ".json", 'description': "File format"},
    }
    
# ####################################################################
#
# Dumper class
#
# ####################################################################

class NetworkDumper(JSONDumper):
    input_specs = {'data' : Network}
    output_specs = {}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Destination of the exported file"},
        'file_format': {"type": str, "default": ".json", 'description': "File format"},
    }