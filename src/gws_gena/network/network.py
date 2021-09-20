# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import re
import json
import uuid
from typing import List, Dict
from pathlib import Path
from pandas import DataFrame
import numpy as np
from typing import TypedDict, Optional

from gws_core import FileImporter, FileExporter, FileLoader, FileDumper, File
from gws_core import Resource, resource_decorator, task_decorator, DictView, SerializedResourceData, StrParam
from gws_core import BadRequestException

from gws_biota import EnzymeClass
from gws_biota import Taxonomy as BiotaTaxo
from .compound import Compound
from .reaction import Reaction

flattening_delimiter = ":"
    
# ####################################################################
#
# Error classes
#
# ####################################################################

class NoCompartmentFound(BadRequestException): 
    pass

class CompoundDuplicate(BadRequestException): 
    pass

class ReactionDuplicate(BadRequestException): 
    pass

NetworkTagDict = TypedDict("NetworkTagDict",{ 
    "reactions": dict, 
    "compounds": dict 
})

NetworkDict = TypedDict("NetworkDict", {
    "name": str,
    "metabolites": dict,
    "reactions": dict,
    "compartments": dict,
    "tags": NetworkTagDict
})

# ####################################################################
#
# Network class
#
# ####################################################################

@resource_decorator("Network",
                    human_name="Network",
                    short_description="Metabolic network",
                    serializable_fields=["uref", "name", "description"])
class Network(Resource):
    """
    Class that represents a network. 
    
    A network is a collection of reconstructed metabolic pathways.
    """
    
    DEFAULT_NAME = "network"
    uref: str = ""
    name: str = DEFAULT_NAME
    description: str = ""

    _compounds: Dict[str, Compound] = None
    _reactions: Dict[str, Reaction] = None
    _compartments: Dict[str, str] = None
    _medium: dict = None
    _stats: dict = None
    _cofactor_freq_threshold = 0.7
    _table_name = "gena_network"

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self._compounds = {}
        self._reactions = {}
        self._compartments = {}
        self._medium = {}
        self.__set_of_chebi_ids = {}
        self.__set_of_ec_numbers = {}
        self.__set_of_rhea_ids = {}
        self._stats = {}

        if "network" in self.binary_store:
            net_dict = self.binary_store["network"]
            self._build_from_dump(net_dict)
        else:
            self.uref = str(uuid.uuid4())
            self.binary_store["network"] = NetworkDict(
                name = self.DEFAULT_NAME,
                metabolites = {},
                reactions = {},
                compartments = {},
                tags =  NetworkTagDict(reactions = {}, compounds = {})
            )

    # -- A --
    
    def add_compound(self, comp: Compound):
        """
        Adds a compound 
        
        :param comp: The compound to add
        :type comp: `gena.network.Compound`
        """
        
        if not isinstance(comp, Compound):
            raise BadRequestException("The compound must an instance of Compound")
        if comp.network and comp.network != self:
            raise BadRequestException("The compound is already in another network")
        if comp.id in self._compounds:
            raise CompoundDuplicate(f"Compound id {comp.id} duplicate")
        if not comp.compartment:
            raise NoCompartmentFound("No compartment defined for the compound")
        if not comp.compartment in self._compartments:
            suffix = comp.compartment.split(Compound.COMPARTMENT_DELIMITER)[-1]
            self.compartments[comp.compartment] = Compound.COMPARTMENTS[suffix]["name"]
        comp.network = self
        self.compounds[comp.id] = comp
        self._stats = {}
        if comp.chebi_id:
            if not comp.compartment in self.__set_of_chebi_ids:
                self.__set_of_chebi_ids[comp.compartment] = {}
            self.__set_of_chebi_ids[comp.compartment][comp.chebi_id] = comp.id
            for _id in comp.alt_chebi_ids:
                self.__set_of_chebi_ids[comp.compartment][_id] = comp.id

    def add_reaction(self, rxn: Reaction):
        """
        Adds a product
        
        :param rxn: The reaction to add
        :type rxn: `gena.network.Reaction`
        """
        
        if not isinstance(rxn, Reaction):
            raise BadRequestException("The reaction must an instance of Reaction")
        if rxn.network:
            raise BadRequestException("The reaction is already in a network")
        if rxn.id in self.reactions:
            raise ReactionDuplicate(f"Reaction id {rxn.id} duplicate")
        
        # add reaction compounds to the network
        for k in rxn.substrates.copy():            
            sub = rxn.substrates[k]
            comp = sub["compound"]
            stoich = sub["stoichiometry"]
            if not self.exists(comp):
                if comp.chebi_id:
                    existing_comp = self.get_compound_by_chebi_id(comp.chebi_id)
                    if existing_comp:
                        # the compound already exists
                        # ... use the existing compound
                        rxn.add_substrate(existing_comp, stoich)
                        rxn.remove_substrate(existing_comp)
                    else:
                        self.add_compound(comp)
                else:
                    self.add_compound(comp)
            
        for k in rxn.products.copy():
            prod = rxn.products[k]
            comp = prod["compound"]
            stoich = sub["stoichiometry"]
            if not self.exists(comp):
                if comp.chebi_id:
                    existing_comp = self.get_compound_by_chebi_id(comp.chebi_id)
                    if existing_comp:
                        # the compound already exists
                        # ... use the existing compound
                        rxn.add_product(existing_comp, stoich)
                        rxn.remove_product(existing_comp)
                    else:
                        self.add_compound(comp)
                else:
                    self.add_compound(comp)
                
        # add the reaction
        rxn.network = self
        self.reactions[rxn.id] = rxn
        self._stats = {}

        if rxn.rhea_id:
            self.__set_of_rhea_ids[rxn.rhea_id] = rxn.id
        if rxn.enzyme:
            ec = rxn.enzyme.get("ec_number")
            if ec:
                self.__set_of_ec_numbers[ec] = rxn.id
              
    # -- B --

    def _build_from_dump_and_set_store(self, net: NetworkDict):
        self._build_from_dump(net)
        self.binary_store["network"] = self.dumps()

    def _build_from_dump(self, data: NetworkDict):
        """
        Build the network from a dump
        """
    
        if not data.get("compartments"):
            raise BadRequestException("Invalid network dump")

        self.compartments = data["compartments"]
        ckey = "compounds" if "compounds" in data else "metabolites"

        added_comps = {}
        for val in data[ckey]:
            compart = val["compartment"]
            if not compart in self.compartments:
                raise BadRequestException(f"The compartment '{compart}' of the compound '{val['id']}' not declared in the lists of compartments")
   
            chebi_id = val.get("chebi_id", "")
            inchikey = val.get("inchikey", "")
            # if re.match(r"CHEBI\:\d+$", val["id"]):
            #     chebi_id = val["id"]

            is_BIGG_data_format = ("annotation" in val)
            alt_chebi_ids = []
            if not chebi_id and not inchikey and is_BIGG_data_format:
                annotation = val["annotation"]
                alt_chebi_ids = annotation.get("chebi",[])
                inchikey = annotation.get("inchi_key", [""])[0]
                if alt_chebi_ids:
                    chebi_id = alt_chebi_ids.pop(0)

            _id = val["id"] #.replace(self.Compound.FLATTENING_DELIMITER,Compound.COMPARTMENT_DELIMITER)
            comp = None
            if chebi_id or inchikey:
                try:
                    comp = Compound.from_biota(
                        id=_id, \
                        name=val.get("name",""), \
                        chebi_id=chebi_id,
                        inchikey=inchikey, \
                        compartment=compart,
                        network=self
                    )
                    if alt_chebi_ids:
                        comp.alt_chebi_ids = alt_chebi_ids
                except:   
                    pass
            
            if comp is None:
                comp = Compound(
                    id=_id, \
                    name=val.get("name",""), \
                    network=self, \
                    compartment=compart,\
                    charge = val.get("charge",""),\
                    mass = val.get("mass",""),\
                    monoisotopic_mass = val.get("monoisotopic_mass",""),\
                    formula = val.get("formula",""),\
                    inchi = val.get("inchi",""),\
                    inchikey = val.get("inchikey",""),\
                    chebi_id = chebi_id,\
                    alt_chebi_ids = alt_chebi_ids,\
                    kegg_id = val.get("kegg_id","")\
                )
            added_comps[_id] = comp

        for val in data["reactions"]:
            rxn = Reaction(
                id=val["id"], #.replace(self.Compound.FLATTENING_DELIMITER,Compound.COMPARTMENT_DELIMITER),\
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
                if re.match(r"CHEBI\:\d+$", comp_id):
                    comps = self.get_compound_by_chebi_id(comp_id)
                    # select the compound in the good compartment
                    for c in comps:
                        if c.compartment == comp.compartment:
                            break

                stoich = val[ckey][comp_id]
                if stoich < 0:
                    rxn.add_substrate( comp, stoich )
                elif stoich > 0:
                    rxn.add_product( comp, stoich )

        self.name = data.get("name", self.DEFAULT_NAME)
        self.description = data.get("description","")

    # -- C --
    
    def copy(self) -> 'Network':
        net: NetworkDict
        net = self.to_json()["network"]
        return Network.from_json(net)
        
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
        
    def create_steady_stoichiometric_matrix(self) -> DataFrame:
        S = self.create_stoichiometric_matrix()
        names = list(self.get_steady_compounds().keys())
        return S.loc[names, :]

    def create_non_steady_stoichiometric_matrix(self, include_biomass=True) -> DataFrame:
        S = self.create_stoichiometric_matrix()
        names = list(self.get_non_steady_compounds().keys())
        return S.loc[names, :]

    # -- D --

    def dumps(self) -> NetworkDict:
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
                "estimate": _rxn.estimate,
                "balance": _rxn.compute_mass_and_charge_balance()
            })
  
        _json = {
            "name": self.name,
            "metabolites": _met_json,
            "reactions": _rxn_json,
            "compartments": self.compartments,
            "tags": self.binary_store["network"]["tags"]
        }
        
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
            
        raise BadRequestException("Invalid element. The element must be an instance of gws.gena.Compound or gws.gena.Reaction")
    
    # -- E --
    
    def export_to_path(self, file_path: str, file_format:str = None):
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
                raise BadRequestException("Invalid file format")
            
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
        if data.get("network"):
            net.uref = data["uref"]
            net._build_from_dump_and_set_store(data["network"])
        else:
            net = Network()  
            net._build_from_dump_and_set_store(data)

        return net
    
    # -- G --
    
    def _get_network_dict_from_store(self):
        return self.binary_store.get("network", NetworkDict())

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
            return self.get_compound_tags().get(comp_id,{}).get(tag_name)
        else:
            return self.get_compound_tags().get(comp_id,{})
        
    def get_compound_tags(self) -> dict:
        """
        Get all the compound tags
        
        :return: The tags
        :rtype: `dict`
        """
        
        return self.binary_store["network"]["tags"]["compounds"]
    
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
            return self.get_reaction_tags().get(rxn_id,{}).get(tag_name)
        else:
            return self.get_reaction_tags().get(rxn_id,{})
        
        
    def get_reaction_tags(self) -> dict:
        """
        Get all the reaction tags
        
        :return: The tags
        :rtype: `dict`
        """
        
        return self.binary_store["network"]["tags"]["reactions"]
    
    def get_compound_by_id(self, comp_id: str) -> Compound:
        """
        Get a compound by its id.
        
        :param comp_id: The compound id
        :type comp_id: `str`
        :return: The compound or `None` if the compond is not found
        :rtype: `gena.network.Compound` or `None`
        """
        
        return self._compounds.get(comp_id)
    
    def get_compound_by_chebi_id(self, chebi_id: str, compartment: str=None)->Compound:
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
        
        if not compartment in self.__set_of_chebi_ids:
            return None
        
        c_id = self.__set_of_chebi_ids[compartment].get(chebi_id)
        if c_id:
            return self._compounds[c_id]
        else:
            return None

        # _list = []
        # for _id in self._compounds:
        #     comp: Compound = self._compounds[_id]
        #     OK = ( comp.chebi_id == chebi_id ) or \
        #          ( chebi_id in comp.alt_chebi_ids )
        #     if OK:
        #         if compartment is None:
        #             _list.append(comp)
        #         elif comp.compartment == compartment:
        #             _list.append(comp)
        # return _list
    
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
        
        r_id = self.__set_of_ec_numbers.get(ec_number)
        if r_id:
            return self._reactions[r_id]
        else:
            return None

        # for k in self._reactions:
        #     rxn = self._reactions[k]
        #     if rxn.ec_number == ec_number:
        #         return rxn

    def get_reaction_by_rhea_id(self, rhea_id: str)->Reaction:
        """
        Get a reaction by its rhea id.
        
        :param rhea_id: The rhea id of the reaction
        :type rhea_id: `str`
        :return: The reaction or `None` if the reaction is not found
        :rtype: `gena.network.Reaction` or `None`
        """
        
        r_id = self.__set_of_rhea_ids.get(rhea_id)
        if r_id:
            return self._reactions[r_id]
        else:
            return None

    def _get_gap_info(self, gap_only=False)->dict:
        """
        Get gap information
        """
        
        from ..recon.gap_finder import GapFinder
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

    # -- H --

    def has_sink(self) -> bool:
        for k in self.compounds:
            comp: Compound = self.compounds[k]
            if comp.is_sink:
                return True
                
    # -- I --

    @classmethod
    def import_from_path(cls, file_path: str, file_format:str = None) -> 'Network':
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
                    raise BadRequestException(f"Cannot load JSON file {file_path}. Error: {err}")  
                if _json.get("reactions"):
                    # is a raw dump network
                    net = cls.from_json(_json)
                elif _json.get("network"): 
                    # is gws resource
                    net = cls.from_json(_json["network"])
                elif _json.get("data",{}).get("network"): 
                    # TODO : Remove after
                    # is gws resource [RETRO COMPATIBILTY]
                    net = cls.from_json(_json["data"]["network"])
                else:
                    raise BadRequestException("Invalid network data")
        else:
            raise BadRequestException("Invalid file format")
        return net
    
    # -- N --

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
    
    def render__compound_stats__as_json(self, stringify=False, **kwargs) -> (dict, str,):
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

    def render__total_abs_flux__as_table(self, stringify=False, **kwargs) -> (str, "DataFrame",):
        total_flux = 0
        for k in self.reactions:
            rxn = self.reactions[k]
            if rxn._estimate:
                total_flux += abs(rxn.estimate["value"])
        return DictView.to_table( {"0": [ total_flux ]}, columns=["total_abs_flux"], stringify=stringify)

    def render__stats__as_json(self, stringify=False, prettify=False, **kwargs) -> (dict, str,):
        if stringify:
            if prettify:
                return json.dumps(self.stats, indent=4)
            else:
                return json.dumps(self.stats)
        else:
            return self.stats
    
    # -- R -- 

    def refresh_binary_store(self):
        self._set_network_dict_in_store( self.dumps() )

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

    def set_reaction_tag(self, tag_id, tag: dict):
        net = self.binary_store["network"]
        if not isinstance(tag, dict):
            raise BadRequestException("The tag must be a dictionary")  
        if not tag_id in net["tags"]["reactions"]:
            net["tags"]["reactions"][tag_id] = {}
        net["tags"]["reactions"][tag_id].update(tag)
        self.binary_store["network"] = net

    def set_compound_tag(self, tag_id, tag: dict):
        net = self.binary_store["network"]
        if not isinstance(tag, dict):
            raise BadRequestException("The tag must be a dictionary")
        if not tag_id in net["tags"]["compounds"]:
            net["tags"]["compounds"][tag_id] = {}
        net["tags"]["compounds"][tag_id].update(tag)
        self.binary_store["network"] = net
        
    def _set_network_dict_in_store(self, net_dict: NetworkDict):
        self.binary_store["network"] = net_dict
        
    # -- T --

    def to_json(self, **kwargs) -> (dict, str,):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param kwargs: Theses parameters are passed to the super class
        :type kwargs: keyword arguments
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(**kwargs)
        _json["network"] = self.dumps() #override to account for new updates
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
        
        return self.to_table().to_csv()
        
    def to_table(self) -> DataFrame:
        """
        Returns a DataFrame representation of the network
        """
        
        bkms = ['brenda', 'kegg', 'metacyc']
        column_names = [
            "id", \
            "equation_str", \
            "enzyme", 
            "ec_number", \
            "lb", \
            "ub", \
            "enzyme_class", \
            "is_from_gap_filling",
            "comments", \
            "substrates", 
            "products", \
            "mass_balance",
            "charge_balance", \
            *BiotaTaxo._tax_tree, \
            *bkms
        ]
        rxn_row = {}
        for k in column_names:
            rxn_row[k] = ""

        table = []
        rxn_count = 1
        for k in self.reactions:
            rxn = self.reactions[k]
            enz = ""
            ec = ""
            comment = []
            enzyme_class = ""
            is_from_gap_filling = False
            pathway_cols = {}
            for f in bkms: 
                pathway_cols[f] = ""

            tax_cols = {}
            for f in BiotaTaxo._tax_tree: 
                tax_cols[f] = ""

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
                    bkms = ['brenda', 'kegg', 'metacyc']
                    pw = rxn.enzyme.get("pathway")
                    if pw:
                        for db in bkms:
                            if pw.get(db):
                                pathway_cols[db] = pw[db]["name"] + " (" + (pw[db]["id"] if pw[db]["id"] else "--") + ")"       
                if rxn.enzyme.get("tax"):
                    tax = rxn.enzyme.get("tax")
                    for f in BiotaTaxo._tax_tree: 
                        if f in tax:
                            tax_cols[f] = tax[f]["name"] + " (" + str(tax[f]["tax_id"]) + ")"
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

            balance = rxn.compute_mass_and_charge_balance()
            _rxn_row = rxn_row.copy()
            _rxn_row["id"] = rxn.id
            _rxn_row["equation_str"] = rxn.to_str()
            _rxn_row["enzyme"] = enz
            _rxn_row["ec_number"] = ec
            _rxn_row["ub"] = str(rxn.lower_bound)
            _rxn_row["lb"] = str(rxn.upper_bound)
            _rxn_row["enzyme_class"] = enzyme_class
            _rxn_row["is_from_gap_filling"] = is_from_gap_filling
            _rxn_row["comments"] = "; ".join(comment)
            _rxn_row["substrates"] = "; ".join(subs)
            _rxn_row["products"] = "; ".join(prods)
            _rxn_row["mass_balance"] = balance["mass"]
            _rxn_row["charge_balance"] = balance["charge"]
            _rxn_row = { **_rxn_row, **tax_cols, **pathway_cols }
            rxn_count += 1
            table.append(list(_rxn_row.values()))
  
        # add the errored ec numbers
        tags = self.get_reaction_tags()
        for k in tags:
            t = tags[k]
            ec = t.get("ec_number")
            is_partial_ec_number = t.get("is_partial_ec_number")
            error = t.get("error")
            if not ec:
                continue
            _rxn_row = rxn_row.copy()
            _rxn_row["ec_number"] = ec       # ec number
            _rxn_row["comments"] = error     # comment
            if is_partial_ec_number:
                try:
                    enzyme_class = EnzymeClass.get(EnzymeClass.ec_number == ec)
                    _rxn_row["enzyme_class"] = enzyme_class.get_name()
                except:
                    pass
            rxn_count += 1
            table.append(list(_rxn_row.values()))
            
        # export
        table = DataFrame(table, columns=column_names)
        table = table.sort_values(by=['ec_number'])
        return table
            

# ####################################################################
#
# Importer class
#
# ####################################################################
    
@task_decorator("NetworkImporter")
class NetworkImporter(FileImporter):
    input_specs = {'file' : File}
    output_specs = {'data': Network}
    config_specs = {
        'file_format': StrParam(default_value=".json", description="File format")
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

@task_decorator("NetworkExporter")
class NetworkExporter(FileExporter):
    input_specs = {'data': Network}
    output_specs = {'file' : File}
    config_specs = {
        'file_name': StrParam(default_value='network.json', description="Destination file name in the store"),
        'file_format': StrParam(default_value=".json", description="File format"),
    }
    
# ####################################################################
#
# Loader class
#
# ####################################################################

@task_decorator("NetworkLoader")
class NetworkLoader(FileLoader):
    input_specs = {}
    output_specs = {'data' : Network}
    config_specs = {
        'file_path': StrParam(default_value=None, description="Location of the file to import"),
        'file_format': StrParam(default_value=".json", description="File format"),
    }
    
# ####################################################################
#
# Dumper class
#
# ####################################################################

@task_decorator("NetworkDumper")
class NetworkDumper(FileDumper):
    input_specs = {'data' : Network}
    output_specs = {}
    config_specs = {
        'file_path': StrParam(default_value=None, description="Destination of the exported file"),
        'file_format': StrParam(default_value=".json", description="File format"),
    }