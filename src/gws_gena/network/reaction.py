# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
import re

from gws_core import BadRequestException
from gws_core import Utils
from gws_biota import Compound as BiotaCompound
from gws_biota import Reaction as BiotaReaction
from gws_biota import Enzyme as BiotaEnzyme
from gws_biota import Taxonomy as BiotaTaxo
from .compound import Compound

def slugify_id(_id):
    return Utils.slugify(_id, snakefy=True, to_lower=False)
    
flattening_delimiter = ":"
EQN_SPLIT_REGEXP = re.compile(" <?=>? ")

# ####################################################################
#
# Error classes
#
# ####################################################################

class SubstrateDuplicate(BadRequestException): 
    pass

class ProductDuplicate(BadRequestException): 
    pass

# ####################################################################
#
# ReactionPosition class
#
# ####################################################################

class ReactionPosition:
    """ reaction position """
    x: float = None
    y: float = None
    z: float = None
    points: str = None

    def __init__(self):
        self.x = None
        self.y = None
        self.z = None
        self.points = {}

    def copy(self) -> 'ReactionPosition':
        p = ReactionPosition()
        p.x = self.x
        p.y = self.y
        p.z = self.z
        p.points = self.points
        return p

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
    
    id: str = ""
    name: str = ""
    network: 'Network' = None
    direction: str = "B"
    lower_bound: float = -1000.0
    upper_bound: float = 1000.0
    rhea_id: str = ""
    enzyme: dict = None
    position: ReactionPosition = None

    _tax_ids = []
    _estimate: dict = None
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
            raise BadRequestException("At least a valid reaction id or name is reaction")
            
        if direction in ["B", "L", "R"]:
            self.direction = direction
            
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self._estimate = {}
        self._substrates = {}
        self._products = {}
        
        if network:
            self.add_to_network(network)
        
        self.rhea_id = rhea_id
        self.position = ReactionPosition()

    # -- A --

    def add_to_network(self, net: 'Network'):  
        """
        Adds the reaction to a newtork
        
        :param net: The network
        :type net: `gena.network.Network`
        """
        
        net.add_reaction(self)

    def add_substrate( self, comp: Compound, stoich: float, update_if_exists=False ):
        """
        Adds a substrate to the reaction
        
        :param comp: The compound to add as substrate
        :type comp: `gena.compound.Compound`
        :param stoich: The stoichiometry of the compound in the reaction
        :type stoich: `int`
        """
        
        if comp.id in self._substrates:
            if update_if_exists:
                self._substrates[comp.id]["stoichiometry"] += abs(float(stoich))
                return
            else:
                raise SubstrateDuplicate("gena.reaction.Reaction", "add_substrate", f"Substrate duplicate (id= {comp.id})")
        
        if comp.id in self._products:
            if update_if_exists:
                self._products[comp.id]["stoichiometry"] -= abs(float(stoich))
                if self._products[comp.id]["stoichiometry"] == 0.0:
                    self.remove_product(comp)
                return
            else:
                raise SubstrateDuplicate("gena.reaction.Reaction", "add_substrate", f"Cannot add the substrate. A product with the id already exists (id= {comp.id})")

        # add the compound to the reaction network
        if self.network:
            if comp.id not in self.network.compounds:
                self.network.add_compound(comp)

        self._substrates[comp.id] = {
            "compound": comp,
            "stoichiometry": abs(float(stoich))
        }
    
    def add_product( self, comp: Compound, stoich: float, update_if_exists=False ):
        """
        Adds a product to the reaction
        
        :param comp: The compound to add as product
        :type comp: `gena.compound.Compound`
        :param stoich: The stoichiometry of the compound in the reaction
        :type stoich: `int`
        """
        
        if comp.id in self._products:
            if update_if_exists:
                self._products[comp.id]["stoichiometry"] += abs(float(stoich))
                return
            else:
                raise ProductDuplicate("gena.reaction.Reaction", "add_product", f"Product duplicate (id= {comp.id})")
        
        if comp.id in self._substrates:
            if update_if_exists:
                self._substrates[comp.id]["stoichiometry"] -= abs(float(stoich))
                if self._substrates[comp.id]["stoichiometry"] == 0.0:
                    self.remove_substrate(comp)
                return
            else:
                raise ProductDuplicate("gena.reaction.Reaction", "add_substrate", f"Cannot add the product. A susbtrate with the id already exists (id= {comp.id})")

        # add the compound to the reaction network
        if self.network:
            if comp.id not in self.network.compounds:
                self.network.add_compound(comp)
                
        self._products[comp.id] = {
            "compound": comp,
            "stoichiometry": abs(float(stoich))
        }

    # -- C --

    def copy(self) -> 'Reaction':
        rxn = Reaction()
        rxn.id = self.id
        rxn.name = self.name
        rxn.network = self.network
        rxn.direction = self.direction
        rxn.lower_bound = self.lower_bound
        rxn.upper_bound = self.upper_bound
        rxn.rhea_id = self.rhea_id
        rxn.enzyme = self.enzyme
        rxn.position = self.position.copy()

        rxn._tax_ids = copy.deepcopy(self._tax_ids)
        rxn._estimate = copy.deepcopy(self._estimate)
        rxn._substrates = copy.deepcopy(self._substrates)
        rxn._products = copy.deepcopy(self._products)
        rxn._products = copy.deepcopy(self._products)
        return rxn

    def compute_mass_and_charge_balance(self) -> dict:
        charge = 0.0
        mass = 0.0
        for sub in self.substrates.values():
            comp: Compound = sub["compound"]
            stoich = sub["stoichiometry"]
            if isinstance(comp.charge, float) and isinstance(charge, float):
                charge += stoich * comp.charge
            else:
                charge = None
            if isinstance(comp.mass, float) and isinstance(mass, float):
                mass += stoich * comp.mass
            else:
                mass = None

        for prod in self.products.values():
            comp: Compound = prod["compound"]
            stoich = prod["stoichiometry"]
            if isinstance(comp.charge, float) and isinstance(charge, float):
                charge -= stoich * comp.charge
            else:
                charge = None
            if isinstance(comp.mass, float) and isinstance(mass, float):
                mass -= stoich * comp.mass
            else:
                mass = None

        return {
            "mass": mass, 
            "charge": charge
        }

    @classmethod
    def create_sink_reaction(self, related_compound: Compound = None, lower_bound: float = -1000.0, upper_bound: float = 1000.0) -> 'Reaction':        
        if not isinstance(related_compound, Compound):
            raise BadRequestException("A compound is required")
        name = related_compound.id + "_sink"
        network = related_compound.network
        rxn = Reaction(
            name = name,
            network = network,
            direction = "B",
            lower_bound = lower_bound,
            upper_bound = upper_bound
        )
        sink_comp = Compound.create_sink_compound(related_compound=related_compound)
        rxn.add_substrate(related_compound, stoich=-1.0)
        rxn.add_product(sink_comp, stoich=1.0)
        return rxn

    # -- E --

    @property
    def estimate(self) -> dict:
        return self._estimate

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
        :rtype: `gena.reaction.Reaction`
        """
        
        rxns = []

        def __create_rxn(rhea_rxn, network, enzyme):
            if enzyme:
                e = {
                    "name": enzyme.get_name(),
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
                        "name": tax.get_name()
                    }
                    for t in tax.ancestors:
                        e["tax"][t.rank] = {
                            "tax_id": t.tax_id,
                            "name": t.get_name()
                        }  
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
            
            rxn: Reaction = cls(name=rhea_rxn.rhea_id+"_"+enzyme.ec_number, 
                      network=network, 
                      direction=rhea_rxn.direction,
                      enzyme=e)
            
            if rhea_rxn.position is not None:
                    rxn.position.x = rhea_rxn.position.x
                    rxn.position.y = rhea_rxn.position.y
                    rxn.position.z = rhea_rxn.position.z
                    rxn.position.points = rhea_rxn.position.points
            
            tab = re.split(EQN_SPLIT_REGEXP, rhea_rxn.data["definition"])
            substrate_definition = tab[0].split(" + ")
            product_definition = tab[1].split(" + ")

            tab = re.split(EQN_SPLIT_REGEXP, rhea_rxn.data["source_equation"])
            eqn_substrates = tab[0].split(" + ")
            eqn_products = tab[1].split(" + ")

            count = 0
            for sub in eqn_substrates:
                tab = sub.split(" ")
                if len(tab) == 2:
                    stoich = tab[0].replace("n","")
                    if stoich == "":
                        stoich = 1.0
                    chebi_ids = tab[1].split(",")
                else:
                    stoich = 1.0
                    chebi_ids = tab[0].split(",")

                biota_comps = []
                for id_ in chebi_ids:
                    biota_comps.append(BiotaCompound.get(BiotaCompound.chebi_id == id_))
                
                if substrate_definition[count].endswith("(out)"):
                    compartment = Compound.COMPARTMENT_EXTRACELL
                else:
                    compartment=Compound.COMPARTMENT_CYTOSOL
                
                c = Compound.merge_compounds(biota_comps, compartment=compartment)
                rxn.add_substrate(c, stoich)
                count += 1

            count = 0
            for prod in eqn_products:
                tab = prod.split(" ")

                if len(tab) == 2:
                    stoich =  tab[0]
                    chebi_ids =  tab[1].split(",")
                else:
                    stoich =  1
                    chebi_ids =  tab[0].split(",")

                biota_comps = []
                for id_ in chebi_ids:
                    biota_comps.append(BiotaCompound.get(BiotaCompound.chebi_id == id_))

                if product_definition[count].endswith("(out)"):
                    compartment = Compound.COMPARTMENT_EXTRACELL
                else:
                    compartment=Compound.COMPARTMENT_CYTOSOL

                c = Compound.merge_compounds(biota_comps, compartment=compartment)
                rxn.add_product(c, stoich)
                count += 1

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
                raise BadRequestException(f"No reaction found with rhea id {rhea_id}")
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
                    raise BadRequestException(f"No taxonomy found with tax_id {tax_id}") 
                Q = BiotaEnzyme.select_and_follow_if_deprecated(ec_number = ec_number, tax_id = tax_id)
                if not Q:
                    if tax_search_method == 'bottom_up':
                        found_Q = []
                        Q = BiotaEnzyme.select_and_follow_if_deprecated(ec_number = ec_number)
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
                    raise BadRequestException(f"No enzyme found with ec number {ec_number}")  
                _added_rxns = []
                for e in Q:
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
                    raise BadRequestException(f"No new reactions found with ec number {ec_number}")  
            else:
                Q = BiotaEnzyme.select_and_follow_if_deprecated(ec_number = ec_number)
                if not Q:
                    raise BadRequestException("gena.reaction.Reaction", "from_biota", f"No enzyme found with ec number {ec_number}")
                _added_rxns = []
                for e in Q:
                    for rhea_rxn in e.reactions:
                        if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                            continue
                        _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                        try:
                            rxns.append( __create_rxn(rhea_rxn, network, e) ) 
                        except:
                            pass
                if not rxns:
                    raise BadRequestException(f"No new reactions found with ec number {ec_number}")
        else:
            raise BadRequestException("gena.reaction.Reaction", "from_biota", "Invalid arguments")
        
        return rxns

    # -- G --

    def get_pathways(self):
        if self.enzyme.get("pathway"):
            return self.enzyme.get("pathway")

        return {}

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
    
    def remove_substrate( self, comp: Compound ):
        """
        Removes a substrate to the reaction
        
        :param comp: The compound to remove
        :type comp: `gena.compound.Compound`
        """
        
        if not comp.id in self._substrates:
            raise BadRequestException(f"Substrate (id= {comp.id}) does not exist")
        
        # remove the compound to the reaction network
        del self._substrates[comp.id]
    
    def remove_product( self, comp: Compound ):
        """
        Remove a product to the reaction
        
        :param comp: The compound to remove
        :type comp: `gena.compound.Compound`
        """
        
        if not comp.id in self._products:
            raise BadRequestException(f"Product (id= {comp.id}) does not exist")
        
        # remove the compound to the reaction network
        del self._products[comp.id]

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
    
    def set_estimate(self, estimate: dict):
        if not "value" in estimate:
            BadRequestException("No value in estimate data")

        if not "lower_bound" in estimate:
            BadRequestException("No lower_bound in estimate data")

        if not "upper_bound" in estimate:
            BadRequestException("No upper_bound in estimate data")

        self._estimate = estimate

    @property
    def substrates(self) -> dict:
        """
        Returns the substrates of the reaction
        
        :return: The list of substrates as {key,value} dictionnary
        :rtype: `dict`
        """
        
        return self._substrates
    
    # -- T --
    
    def to_str(self, show_ids=False, show_mass=False, show_charge=False) -> str:
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
            if show_ids:
                _id = comp.chebi_id if comp.chebi_id else comp.id
                _left.append( f"({stoich}) {_id}" )
            else:
                _left.append( f"({stoich}) {comp.id}" )
        
        for k in self._products:
            prod = self._products[k]
            comp = prod["compound"]
            stoich = prod["stoichiometry"]
            if show_ids:
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
