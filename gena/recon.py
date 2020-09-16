from gws.logger import Logger
from gws.model import Process, ResourceSet, JSONViewModel
from gws.view import JSONViewTemplate

from gaia.datatable import Datatable as D, Importer

from biota.db.enzyme import Enzyme
from biota.db.taxonomy import Taxonomy
from biota.db.enzyme_function import EnzymeFunction

# ####################################################################
#
# Datatable class
#
# ####################################################################

class Datatable(D):
    @property
    def ec_column_name(self):
        return self.data['ec_column_name']

    @ec_column_name.setter
    def ec_column_name(self, name):
        self.data['ec_column_name'] = name

    def get_ec_numbers(self, rtype='list') -> ('DataFrame', list):
        if rtype == 'list':
            return list(self.table[self.ec_column_name].values)
        else:
            return self.table[[self.ec_column_name]]

# ####################################################################
#
# DataImporter class
#
# ####################################################################

class DataImporter(Importer):
    input_specs = {}
    output_specs = {'datatable': Datatable}
    config_specs = {
        **Importer.config_specs,
        'ec_column_name': {"type": 'str', "default": 'ec_number', "description": "The name of the EC Number column name"},
    }

    def task(self):
        super().task()
        dt = self.output['datatable']
        
        if not dt.column_exists( self.get_param('ec_column_name') ):
            Logger.error(Exception("DataImporter", "task", f"No ec numbers found (no column with name '{self.get_param('ec_column_name')}')"))

        dt.ec_column_name = self.get_param('ec_column_name')

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
    def enzyme_functions(self):
        ef = []
        for k in self.enzymes:
            Q = self.enzymes[k].enzyme_functions
            #print(len(Q))
            ef.append(Q[0])
            #for ef in enzyme.enzyme_functions:
                #enzyme_functions.append(ef)
        
        return ef

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
            for ef in self.enzyme_functions:
                #print(ef)
                Q = ef.reactions
                #print(len(Q))

                # @Todo: Check if len(Q) can be 0 ?!!!
                if len(Q) > 0:
                    self._reactions.append(Q[0])

        return self._reactions

    def as_g3_json(self) -> str:

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
                "uri": reac.uri,
                "name": ",".join(reac.data["enzymes"]),
                "metabolites": mets,
                "lower_bound": -1000.0,
                "upper_bound": 1000.0
            })

        for met in self.compounds:
            metabolites.append({
                "id": met.chebi_id,
                "uri": met.uri,
                "name": met.name,
                "compartment": "c"
            })

        genes = []

        import json
        return json.dumps({
            "id": self.id,
            "name": "",
            "version": "",
            "metabolites": metabolites,
            "reactions": reactions,
            "genes": genes,
            "compartments": {
                "c": "cytosol",
                "e": "extracellular space"
            }
        })


# ####################################################################
#
# ViewModel classes
#
# ####################################################################

class G3JSONViewModel(JSONViewModel):
    """
    ...
    """
    model_specs = [ Cell ]

    def as_json(self) -> dict:
        return self._model.as_g3_json()
        

# ####################################################################
#
# CellMaker class
#
# ####################################################################

class CellMaker(Process):
    input_specs = {'datatable': Datatable}
    output_specs = {'cell': Cell}
    config_specs = {
        'tax_ids': {"type": 'list', "default": '[]', "description": "The taxonomy ids of the targeted organisms"},
        'species': {"type": 'list', "default": '[]', "description": "The names of the target species"}
    }

    def task(self):
        dt = self.input['datatable']
        ec_list = dt.get_ec_numbers(rtype="list")
        t = self.output_specs['cell']
        cell = t()

        bulk_size = 100; start = 0
        while True:
            stop = min(start+bulk_size, len(ec_list))

            Q = Enzyme.select().where( Enzyme.ec << ec_list[start:stop] )

            for e in Q:
                cell[e.id] = e
            
            if stop >= len(ec_list):
                break
            
            start = start+bulk_size
 
        self.output["cell"] = cell
