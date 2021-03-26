# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import uuid
from typing import List

from gws.logger import Error
from gws.model import Model, Resource, ResourceSet
from gws.utils import generate_random_chars

from biota.compound import Compound as BiotaCompound
from biota.reaction import Reaction as BiotaReaction
from biota.enzyme import Enzyme as BiotaEnzyme
from biota.taxonomy import Taxonomy as BiotaTaxo


flattening_delimiter = ":"

# ####################################################################
#
# Error class
#
# ####################################################################


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
    
    _flattening_delimiter = flattening_delimiter
    
    def __init__(self, id="", name="", compartment="c", network:'Network'=None, formula="", \
                 charge="", mass="", monoisotopic_mass="", inchi="", \
                 chebi_id="", kegg_id=""):  
        
        if not compartment in self.VALID_COMPARTMENTS:
            raise Error("gena.network.Compound", "__init__", "Invalid compartment")  
        
        self.compartment = compartment   
        

        if id:
            self.id = id
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
                    
                
            self.id = name + "_" + compartment
        
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

        return ctx_name + delim + id.replace(delim,"_")
     
    @classmethod
    def from_biota(cls, chebi_id=None, kegg_id=None) -> 'Compound':
        """
        Create a network compound from a ChEBI of Kegg id
        
        :param chebi_id: The ChEBI id
        :type chebi_id: `str`
        :param kegg_id: The Kegg id
        :type kegg_id: `str`
        :return: The network compound
        :rtype: `gena.network.Compound`
        """
        
        try:
            if chebi_id:
                comp = BiotaCompound.get(BiotaCompound.chebi_id == chebi_id)
            elif kegg_id:
                comp = BiotaCompound.get(BiotaCompound.kegg_id == kegg_id)
            else:
                raise Error("gena.network.Reaction", "from_biota", "Invalid arguments")
        except:
            raise Error("gena.network.Reaction", "from_biota", "Chebi compound not found")
        
        c = cls(name=comp.name)
        c.chebi_id = comp.chebi_id
        c.kegg_id = comp.kegg_id
        c.charge = comp.charge
        c.formula = comp.formula
        c.mass = comp.mass
        c.monoisotopic_mass = comp.monoisotopic_mass
        return c

    
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
                 enzyme: dict={}):  
        
        if id:
            self.id = id
        else:
            self.id = name
        
        self.name = name
        self.enzyme = enzyme
        
        if not self.id:
            if self.enzyme:
                self.id = self.enzyme.get("ec_numner","")
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
        
    # -- A --

    def add_to_network(self, net: 'Network'):  
        """
        Adds the reaction to a newtork
        
        :param net: The network
        :type net: `gena.network.Network`
        """
        
        net.add_reaction(self)
    
    def add_substrate( self, comp: Compound, stoich: int ):
        """
        Adds a substrate to the reaction
        
        :param comp: The compound to add as substrate
        :type comp: `gena.network.Compound`
        :param stoich: The stoichiometry of the compound in the reaction
        :type stoich: `int`
        """
        
        if comp.id in self._substrates:
            raise SubstrateDuplicate("gena.network.Reaction", "add_substrate", "Substrate duplicate")
        
        # add the compound to the reaction network
        if self.network:
            if not comp.id in self.network.compounds:
                self.network.add_compound(comp)
                
        self._substrates[comp.id] = {
            "compound": comp,
            "stoichiometry": abs(int(stoich))
        }
    
    def add_product( self, comp: Compound, stoich: int ):
        """
        Adds a product to the reaction
        
        :param comp: The compound to add as product
        :type comp: `gena.network.Compound`
        :param stoich: The stoichiometry of the compound in the reaction
        :type stoich: `int`
        """
        
        if comp.id in self._products:
            raise ProductDuplicate("gena.network.Reaction", "add_substrate", "Product duplicate")
        
        # add the compound to the reaction network
        if self.network:
            if not comp.id in self.network.compounds:
                self.network.add_compound(comp)
                
        self._products[comp.id] = {
            "compound": comp,
            "stoichiometry": abs(int(stoich))
        }
    
    def as_str(self) -> str:
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
            _left.append( f"({stoich}) {comp.id}" )
        
        for k in self._products:
            sub = self._products[k]
            comp = sub["compound"]
            stoich = sub["stoichiometry"]
            _right.append( f"({stoich}) {comp.id}" )
        
        if not _left:
            _left = ["*"]
            
        if not _right:
            _right = ["*"]
            
        _str = " + ".join(_left) + _dir[self.direction].replace("E", self.enzyme.get("ec_number","")) + " + ".join(_right)
        #_str = _str + " " + str(self.enzyme)
        return _str
    
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
        return ctx_name + delim + id.replace(delim,"_")
        
    @classmethod
    def from_biota(cls, rhea_id=None, ec_number=None, tax_id=None, tax_search_method='bottom_up', network=None) -> 'Reaction':
        """
        Create a biota reaction from a Rhea id or an EC number.
        
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
                        "id": tax.id,
                        "title": tax.title
                    }
                    
                    for t in tax.ancestors:
                        e["tax"][t.rank] = {
                            "id": t.id,
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
                c = Compound(name=biota_comp.name)
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
                c = Compound(name=biota_comp.name)
                c.chebi_id = biota_comp.chebi_id
                c.kegg_id = biota_comp.kegg_id
                c.charge = biota_comp.charge
                c.formula = biota_comp.formula
                c.mass = biota_comp.mass
                c.monoisotopic_mass = biota_comp.monoisotopic_mass
                rxn.add_product(c, stoich)
            
            return rxn
        
        if rhea_id:
            tax = None
            Q = BiotaReaction.select().where(BiotaReaction.rhea_id == rhea_id)
            _added_rxns = []
            for rhea_rxn in Q:
                for e in rhea_rxn.enzymes:
                    if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                        continue
                    _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                    rxns.append( __create_rxn(rhea_rxn, network, e) )

            return rxns
            
        elif ec_number:
            tax = None
            e = None
            
            if tax_id:
                try:
                    tax = BiotaTaxo.get(BiotaTaxo.tax_id == tax_id)
                except:
                    raise Error("Reaction", "from_biota", f"No taxonomy found with tax_id {tax_id}") 
                    #return rxns
                    
                #tax_field = getattr(BiotaEnzyme, "tax_"+tax.rank)
                #Q = BiotaEnzyme.select().where((BiotaEnzyme.ec_number == ec_number) & (tax_field == tax.tax_id))
                
                Q = BiotaEnzyme.select_and_follow_if_deprecated(ec_number = ec_number)
                if not Q:
                    if tax_search_method == 'bottom_up':
                        # search in higher taxonomy levels
                        found_Q = []
                        for t in tax.ancestors:
                            if t.rank == "no rank":
                                continue
                                
                            Q = BiotaEnzyme.select_and_follow_if_deprecated(ec_number = ec_number)
                            for e in Q:
                                if getattr(e, "tax_"+t.rank) == t.tax_id:
                                    found_Q.append(e)
                        
                        Q = found_Q
                            #tax_field = getattr(BiotaEnzyme, "tax_"+t.rank)
                            #Q = BiotaEnzyme.select().where((BiotaEnzyme.ec_number == ec_number) & (tax_field == t.tax_id))
                            #Q = BiotaEnzyme.select_and_follow_if_deprecated(ec_number = ec_number, tax_id = t.tax_id)
                            #if Q:
                            #    break
                
                _added_rxns = []
                for e in Q:
                    for rhea_rxn in e.reactions:
                        if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                            continue
                        _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                        rxns.append( __create_rxn(rhea_rxn, network, e) )
            else:
                #Q = BiotaEnzyme.select().where(BiotaEnzyme.ec_number == ec_number)
                Q = BiotaEnzyme.select_and_follow_if_deprecated(ec_number = ec_number)
                _added_rxns = []
                
                for e in Q:
                    for rhea_rxn in e.reactions:
                        if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                            continue
                        _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                        rxns.append( __create_rxn(rhea_rxn, network, e) ) 
        else:
            raise Error("gena.network.Reaction", "from_biota", "Invalid arguments")

        return rxns

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
    
    _fts_fields = {'title': 2.0, 'description': 1.0}
    _table_name = "gena_network"
    
    _flattening_delimiter = flattening_delimiter
    _defaultNetwork = None
    
    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )

        self._compounds = {}
        self._reactions = {}
        self._compartments = {}
        
        if self.data:
            self.__build_from_dump(self.data["network"])
        else:
            self.data = {
                'title': 'Network',
                'description': '',
                'network': None,
            }
        
        # only used for the reconstruction
        self.data["errored_ec_numbers"] = []
        self.data["partial_ec_numbers"] = []
        self.data["not_found_ec_numbers"] = []
        
    # -- A --
    
    def add_compound(self, comp: Compound):
        """
        Adds a compound 
        
        :param comp: The compound to add
        :type comp: `gena.network.Compound`
        """
        
        if not isinstance(comp, Compound):
            raise Error("Network", "add_compound", "The compound must an instance of Compound")
        
        if comp.network:
            raise Error("Network", "add_compound", "The compound is already in a network")
        
        if comp.id in self._compounds:
            raise CompoundDuplicate("Network", "add_compound", f"Compound id {comp.id} duplicate")
        
        if not comp.compartment:
            raise Error("Network", "add_compound", "No compartment defined for the compound")
            
        comp.network = self
        self.compounds[comp.id] = comp
        
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
        
    
    def as_str(self) -> str:
        """
        Returns a string representation of the network
        
        :rtype: `str`
        """
        
        _str = ""
        for _id in self.reactions:
            _str += "\n" + self.reactions[_id].as_str()
        return _str
    
    def as_csv(self) -> str:
        """
        Returns a CSV representation of the network
        
        :rtype: `str`
        """
        
        return self.as_table(stringify=True)
        
    def as_table(self, stringify=False) -> ('pandas.DataFrame', str):
        """
        Returns a tabular representation of the network
        
        :param stringify: True to stringify the table (as CSV string will be returned). False otherwise
        :type stringify: `bool`
        :rtype: `pandas.DataFrame`, `str`
        """
        
        column_names = [
            "id", "equation", \
            "enzyme", "ec_number", "enzyme_class", \
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
            deprecated_enz = ""
            enzyme_class = ""
            pathway_cols = ["", "", ""]
            tax_cols = [""] * len(BiotaTaxo._tax_tree)
            
            if rxn.enzyme:
                enz = rxn.enzyme.get("title","--") 
                ec = rxn.enzyme.get("ec_number","--")
                
                deprecated_enz = rxn.enzyme.get("related_deprecated_enzyme")
                if deprecated_enz:
                     deprecated_enz = deprecated_enz["ec_number"] + " (" + deprecated_enz["reason"] + ")"

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
                            tax_cols.append( tax[f]["title"] + " (" + str(tax[f]["id"]) + ")" )
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
                rxn.as_str(), \
                enz, ec, \
                enzyme_class, \
                deprecated_enz, \
                "; ".join(subs), \
                "; ".join(prods), \
                *tax_cols, \
                *pathway_cols
            ]
            
            rxn_count += 1
            table.append(rxn_row)
        
        # add the classification of incomplete ec numbers
        from biota.enzyme import EnzymeClass
        partial_ec_numbers = self.data.get("partial_ec_numbers")
        for ec in partial_ec_numbers:
            rxn_row = [""] * len(column_names)
            rxn_row[3] = ec
            try:
                enzyme_class = EnzymeClass.get(EnzymeClass.ec_number == ec)
                rxn_row[4] = enzyme_class.title
            except:
                pass
            
            rxn_row[5] = "partial_ec_numbers"
            rxn_count += 1
            table.append(rxn_row)
        
        # add the errored ec numbers
        errored_ec_numbers = self.data.get("errored_ec_numbers")
        for ec in errored_ec_numbers:
            rxn_row = [""] * len(column_names)
            rxn_row[3] = ec
            rxn_row[5] = "errored_ec_numbers"
            rxn_count += 1
            table.append(rxn_row)
            
        # add the not found ec numbers
        not_found_ec_numbers = self.data.get("not_found_ec_numbers")
        for ec in not_found_ec_numbers:
            rxn_row = [""] * len(column_names)
            rxn_row[3] = ec
            rxn_row[5] = "not_found_ec_numbers"
            rxn_count += 1
            table.append(rxn_row)
            
        # export
        import pandas
        table = pandas.DataFrame(table, columns=column_names)
        
        if stringify:
            return table.to_csv()
        else:
            return table
        
    def as_json(self, stringify=False, prettify=False, **kwargs) -> (dict, str,):
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
        
        _json = super().as_json(**kwargs)
        _json["data"]["network"] = self.dumps() #override to account for new updates
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
                    
    # -- B --
    
    def __build_from_dump(self, data):
        """
        Create a network from a dump
        """
        
        delim = self._flattening_delimiter
        self.compartments = data["compartments"]
        ckey = "compounds" if "compounds" in data else "metabolites"
        for val in data[ckey]:
            compart = val["compartment"]
            
            if not compart in self.compartments:
                raise Error(f"The compartment '{compart}' of the compound '{val['id']}' not declared in the lists of compartments")
            
            comp = Compound(id=val["id"].replace(delim,"_"), \
                            name=val["name"], \
                            network=self, \
                            compartment=compart)
            
        for val in data["reactions"]:
            rxn = Reaction(id=val["id"].replace(delim,"_"), \
                           name=val.get("name"), \
                           network=self, \
                           lower_bound=val.get("lower_bound", Reaction.lower_bound), \
                           upper_bound=val.get("upper_bound", Reaction.upper_bound), \
                           enzyme=val.get("enzyme",{}))
            for k in val[ckey]:
                comp_id = k
                stoich = val[ckey][k]
                if stoich < 0:
                    rxn.add_substrate( self.compounds[comp_id], stoich )
                elif stoich > 0:
                    rxn.add_product( self.compounds[comp_id], stoich )
        
        self.data["name"] = data.get("name","Network").replace(delim,"_")
        self.data["description"] = data.get("description","")
        
    # -- C --
        
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
            #id = _met.id.replace(":","_")
            #if not id.endswith("_"+_met.compartment):
            #    id = id + "_" + _met.compartment
                
            _met_json.append({
                "id": _met.id,
                "name": _met.name,
                "charge": _met.charge,
                "mass": _met.mass,
                "formula": _met.formula,
                "compartment": _met.compartment
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
            
            #id = _rxn.id.replace(":","_")
            _rxn_json.append({
                "id": _rxn.id,
                "name": _rxn.name,
                "enzyme": _rxn.enzyme,
                "metabolites": _rxn_met,
            })
  
        _json = {
            "metabolites": _met_json,
            "reactions": _rxn_json,
            "compartments": self.compartments,
        }
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
        
    # -- F --
    
    @classmethod
    def from_json(cls, data: dict):
        """
        Create a network from a JSON dump
        """
        
        net = Network()
        net.__build_from_dump(data)
        net.data["network"] = net.dumps()
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
    
    def save(self, *args, **kwargs):
        """
        Save the metwork
        """
        
        self.data["network"] = self.dumps()
        return super().save(*args, **kwargs)
    
    
            