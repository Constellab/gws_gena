# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict

from gws_biota import Compartment as BiotaCompartment
from gws_biota import \
    CompartmentNotFoundException as BiotaCompartmentNotFoundException
from gws_core import BadRequestException, SerializableRField

from ..exceptions.compartment_exceptions import InvalidCompartmentException
from ..helper.slugify_helper import SlugifyHelper
from ..typing.compartment_typing import CompartmentDict


class Compartment:
    """
    Compartment class
    Use BiGG DB nomenclature
    """

    CYTOSOL_GO_ID = "GO:0005829"
    BIOMASS_GO_ID = "GO:0016049"
    EXTRACELL_SPACE_GO_ID = "GO:0005615"
    EXTRACELL_REGION_GO_ID = "GO:0005576"
    NUCLEUS_GO_ID = "GO:0005634"
    OTHER_GO_ID = "GO:0005575"
    SINK_GO_ID = "GO:0005576"

    id = None
    go_id = None
    bigg_id = None
    name = None
    is_steady: bool = None

    def __init__(self, dict_: CompartmentDict = None):
        super().__init__()
        if dict_ is None:
            dict_ = {}
        for key, val in dict_.items():
            setattr(self, key, val)

        # only the go_id is used to retreive a valid compartment
        if self.go_id:
            biota_compart = BiotaCompartment.get_by_go_id(go_id=self.go_id)
        else:
            raise InvalidCompartmentException("A valid compartment go_id is required")

        if not self.id:
            self.id = self.go_id

        self.id = SlugifyHelper.slugify_id(self.id)
        self.name = biota_compart.name
        self.is_steady = biota_compart.data["is_steady"]
        self.bigg_id = biota_compart.bigg_id

    def copy(self):
        """ Deep copy the compartment """
        compart = Compartment(
            CompartmentDict(
                id=self.id,
                go_id=self.go_id,
                bigg_id=self.bigg_id,
                name=self.name,
                is_steady=self.is_steady
            ))
        return compart

    def dumps(self) -> Dict:
        """ Dumps as JSON """
        return {
            "id": None,
            "go_id": self.go_id,
            "bigg_id": self.bigg_id,
            "name": self.name
        }

    def loads(self, data: dict) -> 'Compartment':
        """ Loads from as JSON """
        return Compartment(data)

    @classmethod
    def exists(cls, go_id: str = None, bigg_id: str = None):
        """ Returns True if the compartment exists """
        return cls.from_biota(go_id=go_id, bigg_id=bigg_id) is not None

    @classmethod
    def from_biota(cls, *, go_id: str = None, bigg_id: str = None):
        """
        Loads from biota using its `go_id` or `bigg_id`
        The `go_id` is tested in priority if provied
        """

        if (go_id is None) and (bigg_id is None):
            raise BadRequestException("The go_id or bigg_id is required")

        try:
            if go_id:
                biota_compart = BiotaCompartment.get_by_go_id(go_id)
            elif bigg_id:
                biota_compart = BiotaCompartment.get_by_bigg_id(bigg_id)
        except BiotaCompartmentNotFoundException as _:
            return None
        except Exception as err:
            raise BadRequestException("An error occured when fetching compartment from biota") from err

        if biota_compart:
            return Compartment(
                CompartmentDict(
                    go_id=biota_compart.go_id,
                    bigg_id=biota_compart.bigg_id,
                    name=biota_compart.name,
                    is_steady=biota_compart.data["is_steady"]
                ))
        else:
            return None

    @ classmethod
    def create_cytosol_compartment(cls):
        """ Create cytosol compartment """
        return cls.from_biota(go_id=cls.CYTOSOL_GO_ID)

    @ classmethod
    def create_nucleus_compartment(cls):
        """ Create nucleus compartment """
        return cls.from_biota(go_id=cls.NUCLEUS_GO_ID)

    @ classmethod
    def create_biomass_compartment(cls):
        """ Create bioamss compartment """
        return cls.from_biota(go_id=cls.BIOMASS_GO_ID)

    @ classmethod
    def create_extracellular_compartment(cls):
        """ Create extracellular space compartment """
        return cls.from_biota(go_id=cls.EXTRACELL_SPACE_GO_ID)

    @ classmethod
    def create_sink_compartment(cls):
        """ Create extracellular space compartment """
        return cls.from_biota(go_id=cls.SINK_GO_ID)

    def is_extracellular(self) -> bool:
        """
        Test if the compartment is intracellular

        : return: True if the compartment is intracellular, False otherwise
        : rtype: `bool`
        """

        return self.go_id in [self.EXTRACELL_SPACE_GO_ID, self.EXTRACELL_REGION_GO_ID]

    def is_intracellular(self) -> bool:
        """
        Test if the compartment is intracellular

        : return: True if the compartment is intracellular, False otherwise
        : rtype: `bool`
        """

        return self.go_id not in [
            self.EXTRACELL_SPACE_GO_ID, self.EXTRACELL_REGION_GO_ID, self.BIOMASS_GO_ID, self.SINK_GO_ID]

    def is_biomass(self) -> bool:
        """
        Test if the compartment is the biomass compartment

        : return: True if the compartment is the biomass compartment, False otherwise
        : rtype: `bool`
        """

        return self.go_id == self.BIOMASS_GO_ID

    def is_sink(self) -> bool:
        """
        Test if the compartment is a sink compartment

        : return: True if the compartment is a sink compartment, False otherwise
        : rtype: `bool`
        """

        return self.go_id == self.SINK_GO_ID
