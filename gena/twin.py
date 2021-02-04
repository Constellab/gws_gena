# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import uuid
from typing import List

from gws.logger import Error
from gws.model import Model, Process, Resource, ResourceSet
from gws.view import JSONViewTemplate
from gws.utils import generate_random_chars

from biota.db.compound import Compound as BiotaCompound
from biota.db.reaction import Reaction as BiotaReaction
from biota.db.enzyme import Enzyme as BiotaEnzyme, Enzo as BiotaEnzo
from biota.db.taxonomy import Taxonomy

from .data import ECData
from .context import Context

# ####################################################################
#
# Compound class
#
# ####################################################################

class Compound:
                                
    id = None
    name = None
    twin = None
    charge = None
    mass = None
    monoisotopic_mass = None
    formula = None
    inchi = None
    compartment = None
    chebi_id = None
    kegg_id = None
    
    VALID_COMPARTMENTS     = ["c","n","b","e"]
    COMPARTMENT_CYTOSOL    = "c"
    COMPARTMENT_NUCLEUS    = "n"
    COMPARTMENT_BIOMASS    = "b"
    COMPARTMENT_EXTRACELL  = "e"
    
    def __init__(self, id: str=None, name: str=None, twin:'Twin'=None, formula=None, \
                 charge=None, mass=None, monoisotopic_mass=None, inchi=None, \
                 chebi_id=None, kegg_id=None, compartment=None):  
        
        if id:
            self.id = id
        else:
            self.id = str(uuid.uuid4())
            
        if compartment:
            if not compartment in self.VALID_COMPARTMENTS:
                raise Error("Invalid compartment")
                
            self.compartment = compartment
 
        if twin:
            self.add_to_twin(twin)
        
        self.name = name
        self.charge = charge
        self.mass = mass
        self.monoisotopic_mass = monoisotopic_mass
        self.formula = formula
        self.inchi = inchi        
        self.chebi_id = chebi_id
        self.kegg_id = kegg_id
        
    # -- A --

    def add_to_twin(self, tw: 'Twin'):  
        tw.add_compound(self)
        
    # -- F --
    
    @classmethod
    def from_extern(cls, chebi_id=None, kegg_id=None) -> 'Compound':
        try:
            if chebi_id:
                comp = BiotaCompound.get(BiotaCompound.chebi_id == chebi_id)
            elif kegg_id:
                comp = BiotaCompound.get(BiotaCompound.kegg_id == kegg_id)
        except:
            raise Error("gena.twin.Reaction", "from_extern", "Chebi compound not found")
        
        c = cls(id=comp.chebi_id)
        c.chebi_id = comp.chebi_id
        c.kegg_id = comp.kegg_id
        c.name = comp.name
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
    twin: 'Twin' = None
    direction: str = "B"
    lower_bound: float = -1000
    upper_bound: float = 1000
    
    rhea_id = None
    
    _substrates: dict = None
    _products: dict = None
    
    
    def __init__(self, id: str = None, name: str = None, twin: 'Twin' = None, \
                 direction: str= "B", lower_bound: float = -1000, upper_bound: float = 1000):  
        
        if id:
            self.id = id
        else:
            self.id = str(uuid.uuid4())

        if twin:
            self.add_to_twin(twin)
        
        self.name = name
        self.direction = direction
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        
        self._substrates = {}
        self._products = {}

        
    # -- A --

    def add_to_twin(self, tw: 'Twin'):  
        tw.add_reaction(self)
    
    def add_substrate( self, comp: Compound, stoich: float ):
        if comp.id in self._substrates:
            raise Error("gena.twin.Reaction", "add_substrate", "Substrate duplicate")
            
        self._substrates[comp.id] = {
            "compound": comp,
            "stoichiometry": abs(stoich)
        }
    
    def add_product( self, comp: Compound, stoich: float ):
        if comp.id in self._products:
            raise Error("gena.twin.Reaction", "add_substrate", "Product duplicate")
            
        self._products[comp.id] = {
            "compound": comp,
            "stoichiometry": abs(stoich)
        }
    
    # -- F --
    
    @classmethod
    def from_extern(cls, rhea_id=None) -> 'Reaction':
        try:
            if rhea_id:
                comp = BiotaReaction.get(BiotaReaction.rhea_id == rhea_id)
        except:
            raise Error("gena.twin.Reaction", "from_extern", "Chebi compound not found")
        
        rxn = cls(id=comp.rhea_id)

        return rxn

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
        _dir = {"L": " <= ", "R": " => ", "B": " <=> "}
        
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
            
        return " + ".join(_left) + _dir[self.direction] + " + ".join(_right)
    
    @property
    def substrates(self):
        return self._substrates
    
# ####################################################################
#
# Twin class
#
# ####################################################################

class Twin(Resource):
    
    _compounds = None
    _reactions = None
    _compartments = None
    
    _contexts = None
    
    _fts_fields = {'title': 2.0, 'description': 1.0}
    _table_name = "gena_twin"
    

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )

        self._compounds = {}
        self._reactions = {}
        self._compartments = {}
        self._contexts = {}
        
        if self.data:
            self.__build_from_dump(self.data["model"])
        else:
            self.data = {
                'title': '',
                'description': '',
                'model': None,
            }
    
    # -- A --
    
    def add_compound(self, comp: Compound):
        if not isinstance(comp, Compound):
            raise Error("Twin", "add_compound", "The compound must an instance of Compound")
        
        if comp.twin:
            raise Error("Twin", "add_compound", "The compound is already in a twin")
        
        if comp.id in self._compounds:
            raise Error("Twin", "add_compound", f"Compound id {comp.id} duplicate")
        
        if not comp.compartment:
            raise Error("Twin", "add_compound", "No compartment defined for the compound")
            
        comp.twin = self
        self.compounds[comp.id] = comp
        
    def add_reaction(self, rxn: Reaction):
        if not isinstance(rxn, Reaction):
            raise Error("Twin", "add_reaction", "The reaction must an instance of Reaction")
        
        if rxn.twin:
            raise Error("Twin", "add_reaction", "The reaction is already in a twin")
        
        if rxn.id in self.reactions:
            raise Error("Twin", "add_reaction", f"Reaction id {rxn.id} duplicate")
            
        rxn.twin = self
        self.reactions[rxn.id] = rxn
    
    def add_context(self, ctx: 'Context'):
        if not isinstance(ctx, Context):
            raise Error("Twin", "add_context", "The context must an instance of Context")
        
        if ctx.id in self.contexts:
            raise Error("Twin", "add_context", f"Context id {ctx.id} duplicate")
            
        self.contexts[ctx.id] = ctx
        
    #def as_json(self, stringify=False, prettify=False):
    #    _json = super().as_json(stringify, prettify)
    #    return _json
            
    # -- B --
    
    def __build_from_dump(self, data):
        self.compartments = data["compartments"]
        ckey = "compound" if "compound" in data else "metabolites"
        for val in data[ckey]:
            compart = val["compartment"]
            
            if not compart in self.compartments:
                raise Error(f"The compartment of the compound not declared in the lists of compartments")
            
            comp = Compound(id=val["id"], name=val["name"], twin=self, compartment=compart)
            
        for val in data["reactions"]:
            rxn = Reaction(id=val["id"], name=val.get("name"), twin=self, \
                           lower_bound=val.get("lower_bound"), upper_bound=val.get("upper_bound"))
            
            for k in val[ckey]:
                comp_id = k
                stoich = val[ckey][k]
                if stoich < 0:
                    rxn.add_substrate( self.compounds[comp_id], stoich )
                elif stoich > 0:
                    rxn.add_product( self.compounds[comp_id], stoich )
      
        for val in data.get("contexts",{}):
            ctx = Context.get(Context.uri == val["uri"])
            self.add_context(ctx)
        
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
    
    @property
    def contexts(self):
        return self._contexts
    
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
    
    def dumps(self, stringify=False, prettify=False, expand_context=False):
        _met_json = []
        _rxn_json = []
        _ctx_json = []
        
        for _met in self.compounds.values():
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
                
            _rxn_json.append({
                "id": _rxn.id,
                "name": _rxn.name,
                "metabolites": _rxn_met,
            })
        
        for _ctx in self.contexts.values():
            if expand_context:
                _ctx_json.append( _ctx.as_json() )
            else:
                _ctx_json.append( {"uri": _ctx.uri} )
            
        _json = {
            "metabolites": _met_json,
            "reactions": _rxn_json,
            "compartments": self.compartments,
            "contexts": _ctx_json
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
        tw = Twin()
        tw.__build_from_dump(data)
        tw.data["model"] = tw.dumps()
        return tw
    
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
    
    # -- R --
    
    @property
    def reactions(self):
        return self._reactions #self.kv_store["reactions"]
    
    # -- S --
    
    def save(*args, **kwargs):
        self.data["model"] = self.dumps()
        return super().save(*args, **kwargs)