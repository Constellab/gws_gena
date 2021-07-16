# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import List, Dict
from pathlib import Path
from pandas import DataFrame
import numpy as np

from gws.logger import Error
from gws.resource import Resource
from gws.utils import slugify
from gws.view import DictView
from gws.json import *

from biota.enzyme import EnzymeClass
from biota.taxonomy import Taxonomy as BiotaTaxo

from .compound import Compound
from .reaction import Reaction

flattening_delimiter = ":"
    
# ####################################################################
#
# Error classes
#
# ####################################################################

class NoCompartmentFound(Error): 
    pass

class CompoundDuplicate(Error): 
    pass

class ReactionDuplicate(Error): 
    pass

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
    
    _compounds: Dict[str, Compound] = None
    _reactions: Dict[str, Reaction] = None
    _compartments: Dict[str, str] = None
    _medium = None
    
    #_fts_fields = {'title': 2.0, 'description': 1.0}
    _table_name = "gena_network"
    
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
                'name': 'Network_' + self.uri,
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
            self.compartments[comp.compartment] = comp.compartment
        
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
                    comp = Compound.from_biota(
                        id=val["id"].replace(delim,"_"), \
                        name=val.get("name",""), \
                        chebi_id=chebi_id,
                        compartment=compart,
                        network=self
                    )
                except:
                    pass
                 
            if not comp:   
                comp = Compound(
                    id=val["id"].replace(delim,"_"), \
                    name=val.get("name",""), \
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
            
            if val.get("estimate"):
                rxn.set_estimate(val.get("estimate"))

            for comp_id in val[ckey]:
                comp = added_comps[comp_id]
                
                # search according to compound ids
                if "CHEBI:" in comp_id:
                    comps = self.get_compounds_by_chebi_id(comp_id)
                    # select the compound in the good compartment
                    for c in comps:
                        if c.compartment == comp.compartment:
                            break
                
                #print(comp_id)
                #print("--" + str(comp))
                #print("--" + comp.id)
                #print("--" + comp.name)
                #print("--" + comp.compartment)

                stoich = val[ckey][comp_id]
                if stoich < 0:
                    rxn.add_substrate( comp, stoich )
                elif stoich > 0:
                    rxn.add_product( comp, stoich )

            #print(rxn.to_str())

        self.data["name"] = data.get( "name", "Network_"+self.uri ).replace(delim,"_")
        self.data["description"] = data.get("description","")
        
        if data.get("tags"):
            self.data["tags"] = data.get("tags")
        
    # -- C --
    
    def copy(self) -> 'Network':
        return Network.from_json( self.to_json()["data"]["network"] )
        
    @property
    def compartments(self) -> Dict[str, str]:
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
    def compounds(self) -> Dict[str, Compound]:
        """
        Returns the list of compounds
        
        :rtype: `dict`
        """
        
        return self._compounds
    
    def create_stoichiometric_matrix(self) -> DataFrame:
        rxn_ids = list(self.reactions.keys())
        comp_ids = list(self.compounds.keys())
        S = DataFrame(
            index = comp_ids,
            columns = rxn_ids,
            data = np.zeros((len(comp_ids),len(rxn_ids)))
        )

        for rxn_id in self.reactions:
            rxn = self.reactions[rxn_id]
            for comp_id in rxn._substrates:
                val = rxn._substrates[comp_id]["stoichiometry"]
                S.at[comp_id, rxn_id] = -val

            for comp_id in rxn._products:
                val = rxn._products[comp_id]["stoichiometry"]
                S.at[comp_id, rxn_id] = val

        return S
        
    #def create_intracell_stoichiometric_matrix(self) -> DataFrame:
    def create_steady_stoichiometric_matrix(self) -> DataFrame:
        S = self.create_stoichiometric_matrix()
        names = list(self.get_steady_compounds().keys())
        return S.loc[names, :]

    #def create_extracell_stoichiometric_matrix(self, include_biomass=True) -> DataFrame:
    def create_non_steady_stoichiometric_matrix(self, include_biomass=True) -> DataFrame:
        S = self.create_stoichiometric_matrix()
        names = list(self.get_non_steady_compounds().keys())
        return S.loc[names, :]

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
                "lower_bound": _rxn.lower_bound,
                "upper_bound": _rxn.upper_bound,
                "estimate": _rxn.estimate
            })
  
        _json = {
            "name": self.name,
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
        
        if data.get("data",{}).get("network"):
            # data is a full json export
            data = data["data"]["network"]
        
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
    
    def get_compound_ids(self) -> List[str]:
        return [ _id for _id in self._compounds ]

    def get_reaction_ids(self) -> List[str]:
        return [ _id for _id in self._reactions ]

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

    def _get_gap_info(self, gap_only=False)->dict:
        """
        Get gap information
        """
        
        from gena.gap_find import GapFinder
        return GapFinder.extract_gaps(self)
    
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

    def get_biomass_compound(self) -> Compound:
        """ 
        Get the biomass compounds if it exists
        
        :returns: The biomass compounds
        :rtype: `gena.network.Compound`
        """

        for name in self.compounds:
            name_lower = name.lower()
            if name_lower.endswith("_b") or name_lower == "biomass":
                return self.compounds[name]
        return None

    def get_compounds_by_compartments(self, compartment_list:List[str] = None) -> Dict[str, Compound]:
        """
        Get the compounds in a compartments
        
        :returns: The list of compounds
        :rtype: List[`gena.network.Compound`]
        """

        comps = {}
        for name in self.compounds:
            comp = self.compounds[name]
            if comp.compartment in compartment_list:
                comps[name] = self.compounds[name]
        return comps

    def get_steady_compounds(self) -> Dict[str, Compound]:
        """ 
        Get the steady compounds
        
        :returns: The list of steady compounds
        :rtype: List[`gena.network.Compound`]
        """

        comps = {}
        for name in self.compounds:
            comp = self.compounds[name]
            if comp.is_steady:
                comps[name] = self.compounds[name]
        return comps

    def get_non_steady_compounds(self) -> Dict[str, Compound]:
        """ 
        Get the non-steady compounds
        
        :returns: The list of non-steady compounds
        :rtype: List[`gena.network.Compound`]
        """

        comps = {}
        for name in self.compounds:
            comp = self.compounds[name]
            if not comp.is_steady:
                comps[name] = self.compounds[name]
        return comps

    def get_reaction_bounds(self) -> DataFrame:
        """
        Get the reaction bounds `[lb, ub]`

        :return: The reaction bounds
        :rtype: `DataFrame`
        """

        bounds = DataFrame(
            index = self.get_reaction_ids(),
            columns = ["lb", "ub"],
            data = np.zeros((len(self.reactions),2))
        )
        for k in self.reactions:
            rxn: Reaction = self.reactions[k]
            bounds.loc[k,:] = [ rxn.lower_bound, rxn.upper_bound ] 
        return bounds

    def get_number_of_reactions(self) -> int:
        return len(self.reactions)

    def get_number_of_compounds(self) -> int:
        return len(self.compounds)

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
        
        :return: The name
        :rtype: `str`
        """
        
        return self.data.get("name", "")
    
    @name.setter
    def name(self, name:str):
        """ 
        Set the name of the compartment.
        
        :param name: The name
        :type name: `str`
        """
        
        self.data["name"] = name
    
    # -- P --
    
    # -- R --
    
    @property
    def reactions(self) -> Dict[str, Reaction]:
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
    
    def render__compound_stats__as_json(self, stringify=False, prettify=False, **kwargs) -> (dict, str,):
        return self.stats["compounds"]
    
    def render__compound_stats__as_table(self, stringify=False, **kwargs) -> (str, "DataFrame",):
        _dict = self.stats["compounds"]
        for comp_id in _dict:
            _dict[comp_id]["chebi_id"] = self._compounds[comp_id].chebi_id
        table = DictView.to_table(_dict, columns=["count", "freq", "chebi_id"], stringify=False)
        table = table.sort_values(by=['freq'], ascending=False)
        if stringify:
            return table.to_csv()
        else:
            return table
    
    def render__gaps__as_json(self, stringify=False, **kwargs) -> (str, "DataFrame",):
        return self._get_gap_info()
    
    def render__gaps__as_table(self, stringify=False, **kwargs) -> (str, "DataFrame",):
        _dict = self._get_gap_info()
        return DictView.to_table(_dict, columns=["is_substrate", "is_product", "is_gap"], stringify=stringify)

    def render__total_flux__as_table(self, stringify=False, **kwargs) -> (str, "DataFrame",):
        total_flux = 0
        for k in self.reactions:
            rxn = self.reactions[k]
            if rxn._estimate:
                total_flux += abs(rxn.estimate["value"])
        return DictView.to_table( {"0": [ total_flux ]}, columns=["total_flux"], stringify=stringify)

    def render__stats__as_json(self, stringify=False, prettify=False, **kwargs) -> (dict, str,):
        if stringify:
            if prettify:
                return json.dumps(self.stats, indent=4)
            else:
                return json.dumps(self.stats)
        else:
            return self.stats
    
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
            "lb", "ub", \
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
                enz = rxn.enzyme.get("name","--") 
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
                            tax_cols.append( tax[f]["name"] + " (" + str(tax[f]["tax_id"]) + ")" )
                        else:
                            tax_cols.append("")
                if rxn.enzyme.get("ec_number"):
                    try:
                        enzyme_class = EnzymeClass.get(EnzymeClass.ec_numbner == rxn.enzyme.get("ec_number"))
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
                str(rxn.lower_bound), str(rxn.upper_bound), \
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
                    rxn_row[4] = enzyme_class.get_name()
                except:
                    pass
            rxn_count += 1
            table.append(rxn_row)
            
        # export
        table = DataFrame(table, columns=column_names)
        table = table.sort_values(by=['ec_number'])
        if stringify:
            return table.to_csv()
        else:
            return table


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