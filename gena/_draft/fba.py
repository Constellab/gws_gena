# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from .twin import Twin, Compound, Reaction

# ####################################################################
#
# FbaModel class
#
# ####################################################################

class FbaModel(Twin):
    
    
    # -- I --

    @classmethod
    def _import(cls, file_path: str, delimiter: str="\t", header=0, index_col=None, file_format:str = None) -> any:
        """ 
        Import from a repository

        :param file_path: The source file path
        :type file_path: File
        :returns: the parsed data
        :rtype any
        """

        file_extension = Path(file_path).suffix
        
        if file_extension in [".json"] or file_format in [".json"] :
            t = Twin()
            
            with open(file_path) as f:
                _json = json.load(f)
                
                for k in _json["compartments"]:
                    compart = _json["compartments"][k]
                    c = Compartament(twin=t)
                    
                for k in _json["metabolites"]:
                    met = _json["metabolites"][k]
                    comp = Compound(id=met.id, twin=t, )
        else:
            raise Error("FbaModel", "_import", "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")
        
        return cls(table=df)


# ####################################################################
#
# FbaModelMaker class
#
# ####################################################################

class FbaModelMaker(Process):
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