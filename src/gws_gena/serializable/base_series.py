# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Type

from gws_biota import CompoundLayout as BiotaCompoundLayout
from gws_core import BadRequestException, SerializableObjectJson


class BaseSeries(SerializableObjectJson):
    """ BaseSeries """

    _elements: Dict[str, Any] = None
    _serialized_attrs: List = None

    def __init__(self, elements: Dict[str, Any] = None):
        super().__init__()
        self._elements = {}
        if elements is not None:
            for key, val in elements.items():
                elt_type: Type = self.get_element_type()
                self._elements[key] = elt_type(val)

    def copy(self) -> Any:
        """ Copy the BaseSeries """
        return self.deserialize(self.serialize())

    def get_elements(self) -> dict:
        """ Get all elements """
        return self._elements

    def __delitem__(self, key: str):
        del self._elements[key]

    def __len__(self):
        return len(self._elements)

    def __getitem__(self, key):
        """ Get an element """
        return self._elements[key]

    def __contains__(self, key: str):
        """ Exists """
        return key in self._elements

    def __setitem__(self, key, elt: Any):
        """ Set an element """
        if not issubclass(type(elt), self.get_element_type()):
            raise BadRequestException(f"The element must be an instance of {type(elt).__name__}")
        self._elements[key] = elt

    def serialize(self) -> Dict:
        """
        Serialize
        """

        _dict = {}
        for _id, elt in self._elements.items():
            _dict[_id] = {k: getattr(elt, k) for k in self.get_fields_to_serialize()}
        return _dict

    @ classmethod
    def deserialize(cls, data: Dict[str, dict]) -> 'BaseSeries':
        """ Deserialize """
        if data is None:
            return {}
        return cls(data)

    # METHODS TO OVERRIDE

    @classmethod
    def get_fields_to_serialize(cls) -> List:
        """
        Get the element attributes to serilize

        To override
        """
        return []

    @classmethod
    def get_element_type(cls) -> Type:
        """
        Get the type the element to serialize

        To override
        """
