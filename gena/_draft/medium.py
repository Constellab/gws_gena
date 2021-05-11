# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import uuid
from typing import List

from gws.logger import Error

# ####################################################################
#
# Variable class
#
# ####################################################################

class Medium:
    
    _compounds = {}
    
    def __init__( self):
        pass
    
    def add_compound(self, comp: 'Compound'):
        """
        Adds a compound to medium
        
        :param comp: The compound
        :type comp: `gena.network.Compound`
        """
        from .network import Compound
        
        if isinstance(comp, Compound):
            raise Error("Medium", "add_compound", "A compound is required")
            
        self._compounds[comp.id] = comp
      
    def as_json(self):
        pass
    
    @classmethod
    def from_csv(cls, medium: dict):
        pass
    
    @classmethod
    def from_json(cls, medium: dict):
        """
        Adds a compound to medium
        
        :param comp: The compound
        :type comp: `gena.network.Compound`
        """
        
        m = Medium()
        for k in self.medium:
            m._compounds[k] = self.medium[k]
        
        return m