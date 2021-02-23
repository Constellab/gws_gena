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

from biota.db.compound import Compound as BiotaCompound
from biota.db.reaction import Reaction as BiotaReaction
from biota.db.enzyme import Enzyme as BiotaEnzyme
from biota.db.taxonomy import Taxonomy as BiotaTaxo


flattening_delimiter = ":"

# ####################################################################
#
# Compound class
#
# ####################################################################

class Compound:
                                
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
    
    def __init__(self, id=None, name="unnamed", compartment="c", network:'Network'=None, formula=None, \
                 charge=None, mass=None, monoisotopic_mass=None, inchi=None, \
                 chebi_id=None, kegg_id=None):  
        
        if not compartment in self.VALID_COMPARTMENTS:
            raise Error("gena.network.Compound", "__init__", "Invalid compartment")  
        
        self.compartment = compartment   
        
        if id:
            self.id = id
        else:
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

    def add_to_network(self, tw: 'Network'):  
        tw.add_compound(self)
        
    # -- F --
    
    @classmethod
    def _flatten_id(cls, id, ctx_name, is_compartment=False):
        delim = cls._flattening_delimiter
        skip_list = [ cls.COMPARTMENT_EXTRACELL ]
        for c in skip_list:
            if id.endswith("_" + c) or (is_compartment and id == c):
                return id

        return ctx_name + delim + id.replace(delim,"_")
     
    @classmethod
    def from_biota(cls, chebi_id=None, kegg_id=None) -> 'Compound':
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
    id: str = None
    name: str = None
    network: 'Network' = None
    direction: str = "B"
    lower_bound: float = -1000.0
    upper_bound: float = 1000.0
    rhea_id = None
    ec_number = ""
    source_tax = { "id": "", "title": "", "rank": "", "distance": 0.0 }
    
    _tax_ids = []
    _substrates: dict = None
    _products: dict = None
    _flattening_delimiter = flattening_delimiter
    
    def __init__(self, id: str=None, name: str = None, network: 'Network' = None, \
                 direction: str= "B", lower_bound: float = -1000.0, upper_bound: float = 1000.0, \
                 ec_number=""):  
        
        if id:
            self.id = id
        else:
            self.id = name
            
        self.name = name
        if direction in ["B", "L", "R"]:
            self.direction = direction
            
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.ec_number = ec_number
        
        self._substrates = {}
        self._products = {}
        
        if network:
            self.add_to_network(network)
        
    # -- A --

    def add_to_network(self, tw: 'Network'):  
        tw.add_reaction(self)
    
    def add_substrate( self, comp: Compound, stoich: float ):
        if comp.id in self._substrates:
            raise Error("gena.network.Reaction", "add_substrate", "Substrate duplicate")
        
        # add the compound to the reaction network
        if self.network:
            if not comp.id in self.network.compounds:
                self.network.add_compound(comp)
                
        self._substrates[comp.id] = {
            "compound": comp,
            "stoichiometry": abs(float(stoich))
        }
    
    def add_product( self, comp: Compound, stoich: float ):
        if comp.id in self._products:
            raise Error("gena.network.Reaction", "add_substrate", "Product duplicate")
        
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
    def _flatten_id(cls, id, ctx_name):
        delim = cls._flattening_delimiter
        return ctx_name + delim + id.replace(delim,"_")
        
    @classmethod
    def from_biota(cls, rhea_id=None, ec_number=None, tax_id=None, tax_search_method='bottom_up', network=None) -> 'Reaction':
        """
        Returns a reaction using biota DB
        
        :param rhea_id: The ID of the Rhea reaction to fetch. If given, the other parameters are not considered
        :rtype rhea_id: `str`
        :param ec_number: The EC number of the enzyme related to the reaction. If given, all the Rhea reactions associated with this enzyme are retrieved
        :rtype ec_number: `str`
        :param tax_id: The taxonomy ID of the target organism. If given, the enzymes are fetched in the corresponding taxonomy. If the taxonomy ID is not valid, no reaction is built.  
        :rtype tax_id: `str`
        :param tax_search_method: The taxonomy search method (Defaults to `bottom_up`). 
            * `none`: the algorithm will only search at the given taxonomy level
            * `bottom_up`: the algorithm will to traverse the taxonomy tree to search in the higher taxonomy levels until a reaction is found
        :rtype tax_search_method: `none` or `bottom_up`
        :param network: The network to which the reaction is added. If the reaction already exists, an exception is raised.
        :rtype network: `Network`
        """
        
        rxns = []
        tax_tree = BiotaTaxo._tax_tree
        
        def __create_rxn(rhea_rxn, network, enzyme, tax=None, distance=0.0):
            rxn = cls(name=rhea_rxn.rhea_id+"_"+enzyme.ec_number, 
                      network=network, 
                      direction=rhea_rxn.direction,
                      ec_number = enzyme.ec_number)
            if tax:
                rxn.source_tax = { "id": tax.tax_id, "title": tax.title, "rank": tax.rank, "distance": distance }
            else:
                rxn.source_tax = Reaction.source_tax.copy()
                
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
            e = None
            
            if tax_id:
                try:
                    tax = BiotaTaxo.get(BiotaTaxo.tax_id == tax_id)
                except:
                    return rxns
                
                tax_field = getattr(BiotaEnzyme, "tax_"+tax.rank)
                Q = BiotaEnzyme.select().where((BiotaEnzyme.ec_number == ec_number) & (tax_field == tax.tax_id))
                
                distance = 0.0
                    
                if not Q:
                    if tax_search_method == 'bottom_up':
                        # search in higher taxonomy levels
                        for t in tax.ancestors:
                            distance = distance + 1.0
                            if t.rank == "no rank":
                                return rxns

                            tax_field = getattr(BiotaEnzyme, "tax_"+t.rank)
                            Q = BiotaEnzyme.select().where((BiotaEnzyme.ec_number == ec_number) & (tax_field == t.tax_id))
                            if Q:
                                tax = t
                                break
                
                _added_rxns = []
                for e in Q:
                    for rhea_rxn in e.reactions:
                        if (rhea_rxn.rhea_id + e.ec_number) in _added_rxns:
                            continue
                        _added_rxns.append(rhea_rxn.rhea_id + e.ec_number)
                        rxns.append( __create_rxn(rhea_rxn, network, e, tax, distance) )
            else:
                Q = BiotaEnzyme.select().where(BiotaEnzyme.ec_number == ec_number)
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
    def products(self):
        return self._products
    
    # -- R --
    
    def get_related_biota_compound(self):
        try:
            if self.chebi_id:
                return BiotaCompound.get(BiotaCompound.chebi_id == self.chebi_id)
            elif self.kegg_id:
                return BiotaCompound.get(BiotaCompound.kegg_id == self.kegg_id)
        except:
            return None
    
    # -- S --
    
    def __str__(self):
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
            
        _str = " + ".join(_left) + _dir[self.direction].replace("E", self.ec_number) + " + ".join(_right)
        _str = _str + " " + str(self.source_tax)
        return _str
    
    @property
    def substrates(self):
        return self._substrates
    
# ####################################################################
#
# Network class
#
# ####################################################################

class Network(Resource):
    
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
    
    # -- A --
    
    def add_compound(self, comp: Compound):
        if not isinstance(comp, Compound):
            raise Error("Network", "add_compound", "The compound must an instance of Compound")
        
        if comp.network:
            raise Error("Network", "add_compound", "The compound is already in a network")
        
        if comp.id in self._compounds:
            raise Error("Network", "add_compound", f"Compound id {comp.id} duplicate")
        
        if not comp.compartment:
            raise Error("Network", "add_compound", "No compartment defined for the compound")
            
        comp.network = self
        self.compounds[comp.id] = comp
        
    def add_reaction(self, rxn: Reaction):
        if not isinstance(rxn, Reaction):
            raise Error("Network", "add_reaction", "The reaction must an instance of Reaction")
        
        if rxn.network:
            raise Error("Network", "add_reaction", "The reaction is already in a network")
        
        if rxn.id in self.reactions:
            raise Error("Network", "add_reaction", f"Reaction id {rxn.id} duplicate")
        
        # add reaction compounds to the network
        for sub in rxn.substrates:
            comp = sub["compound"]
            if not comp.id in self.compounds:
                self.add_compound(comp)
        
        for prod in rxn.products:
            comp = prod["compound"]
            if not comp.id in self.compounds:
                self.add_compound(comp)
                
        # add the reaction
        rxn.network = self
        self.reactions[rxn.id] = rxn
        
        

    def as_json(self, stringify=False, prettify=False):
        _json = super().as_json()
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
                           ec_number=val.get("ec_number",""))
            rxn.source_tax = val.get("source_tax", Reaction.source_tax.copy())
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
        return self._compartments
    
    @compartments.setter
    def compartments(self, val):
        self._compartments = val
    
    @property
    def compounds(self):
        return self._compounds
    
    # -- D --

    @property
    def description(self) -> str:
        """ 
        Set the description of the compartment.
        
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
                "ec_number": _rxn.ec_number,
                "source_tax": _rxn.source_tax,
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
    
    def print(self):
        s = ""
        for _id in self.reactions:
            s = s + "\n" + str(self.reactions[_id])
        
        print(s)
        
        
    # -- R --
    
    @property
    def reactions(self):
        return self._reactions #self.kv_store["reactions"]
    
    # -- S --
    
    def save(self, *args, **kwargs):
        self.data["network"] = self.dumps()
        return super().save(*args, **kwargs)
    
    
            