import json

from gws.logger import Error
from gws.model import Process, ResourceSet
from gws.view import JSONViewTemplate

from biota.db.enzyme import Enzyme
from biota.db.taxonomy import Taxonomy
from biota.db.enzyme import Enzyme


from .data import ECData

# ####################################################################
#
# Cell class
#
# ####################################################################

class Cell(ResourceSet):

    _compounds = None
    _reactions = None
    
    @property
    def enzymes(self):
        return self.set

    @property
    def compounds(self):
        if self._compounds is None:
            self._compounds = []
            for reac in self.reactions:
                Q = reac.substrates
                for c in Q:
                    if not c in self._compounds:
                        self._compounds.append(c)

                Q = reac.products
                for c in Q:
                    if not c in self._compounds:
                        self._compounds.append(c)

        return self._compounds

    @property
    def reactions(self):
        if self._reactions is None:
            self._reactions = []
            for enzyme in self.enzymes.values():
                Q = enzyme.reactions
                #print(len(Q))

                # @Todo: Check if len(Q) can be 0 ?!!!
                if len(Q) > 0:
                    self._reactions.append(Q[0])

        return self._reactions
    
    def as_json(self, stringify: bool = False, prettify: bool = False, bare:bool = False) -> str:

        reactions = []
        metabolites = []
        for reac in self.reactions:
            mets = {}
            eq = reac.data["equation"]
            for chebi_id in eq["substrates"]:
                stoich = eq["substrates"][chebi_id]
                mets[chebi_id] = - int(stoich)

            for chebi_id in eq["products"]:
                stoich = eq["products"][chebi_id]
                mets[chebi_id] = int(stoich)

            if reac.rhea_id is None:
                reac_id = reac.id
            else:
                reac_id = reac.rhea_id

            reactions.append({
                "id": reac_id,
                "uri": "" if bare else reac.uri,
                "name": ",".join(reac.data["enzymes"]),
                "metabolites": mets,
                "lower_bound": -1000.0,
                "upper_bound": 1000.0
            })

        for met in self.compounds:
            metabolites.append({
                "id": met.chebi_id,
                "uri": "" if bare else met.uri,
                "name": met.get_title(),
                "compartment": "c"
            })

        genes = []

        _json = {
            "uri": "" if bare else self.uri,
            "name": "",
            "version": "",
            "metabolites": metabolites,
            "reactions": reactions,
            "genes": genes,
            "compartments": {
                "c": "cytosol",
                "e": "extracellular space"
            }
        }
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

# ####################################################################
#
# CellMaker class
#
# ####################################################################

class CellMaker(Process):
    input_specs = {'ec_data': ECData}
    output_specs = {'cell': Cell}
    config_specs = {
        'tax_ids': {"type": 'list', "default": '[]', "description": "The taxonomy ids of the targeted organisms"},
        'species': {"type": 'list', "default": '[]', "description": "The names of the target species"}
    }

    async def task(self):
        dt = self.input['ec_data']
        ec_list = dt.get_ec_numbers(rtype="list")
        t = self.output_specs['cell']
        cell = t()

        bulk_size = 100; start = 0
        while True:
            stop = min(start+bulk_size, len(ec_list))
            Q = Enzyme.select().where( Enzyme.ec_number << ec_list[start:stop] )

            for e in Q:
                if not e.ec_number in cell:
                    cell[e.ec_number] = e
            
            if stop >= len(ec_list):
                break
            
            start = start+bulk_size

        self.output["cell"] = cell

    def _check_mass_balance( self, cell ):
        return cell

    def _compute_metabolite_mass( self, cell ):
        return cell
        
    def _compute_metabolite_mass( self, cell ):
        return cell
