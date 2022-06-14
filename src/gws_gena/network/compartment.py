# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import BadRequestException, Utils

from .helper.slugify_helper import SlugifyHelper

# ####################################################################
#
# Compartment class
#
# ####################################################################


class InvalidCompartmentException(BadRequestException):
    """ InvalidCompartmentException """


class Compartment:
    """
    Compartment class
    Use BiGG DB nomenclature
    """

    DELIMITER = "_"

    CYTOSOL = "c"
    NUCLEUS = "n"
    MITOCHONDRIA = "m"
    BIOMASS = "b"
    EXTRACELLULAR_SPACE = "e"
    SINK = "s"
    PERIPLASM = "p"

    COMPARTMENTS = {
        "b": {"name": "biomass", "is_steady": False},
        "c": {"name": "cytosol", "is_steady": True},
        "cm": {"name": "cytosolic membrane", "is_steady": True},
        "cx": {"name": "carboxyzome", "is_steady": True},
        "e": {"name": "extracellular space", "is_steady": False},
        "g": {"name": "golgi apparatus", "is_steady": True},
        "h": {"name": "chloroplast", "is_steady": True},
        "f": {"name": "flagellum", "is_steady": True},
        "i": {"name": "inner mitochondrial compartment", "is_steady": True},
        "im": {"name": "mitochondrial intermembrane space", "is_steady": True},
        "l": {"name": "lysosome", "is_steady": True},
        "m": {"name": "mitochondria", "is_steady": True},
        "mm": {"name": "mitochondria intermembrane", "is_steady": True},
        "n": {"name": "nucleus", "is_steady": True},
        "o": {"name": "other", "is_steady": True},
        "p": {"name": "periplasm", "is_steady": True},
        "r": {"name": "endoplasmic reticulum", "is_steady": True},
        "s": {"name": "eyespot", "is_steady": True},
        "sk": {"name": "sink", "is_steady": False},
        "u": {"name": "thylakoid", "is_steady": True},
        "um": {"name": "thylakoid membrane", "is_steady": True},
        "v": {"name": "vacuole", "is_steady": True},
        "x": {"name": "peroxisome/glyoxysome", "is_steady": True},
        "y": {"name": "cytochrome complex", "is_steady": True}
    }

    @classmethod
    def check_and_retrieve_suffix(cls, compartment):
        """ Check compartment """
        if len(compartment) == 1:
            if compartment not in cls.COMPARTMENTS:
                raise InvalidCompartmentException(f"Invalid compartment '{compartment}'")
            compartment_suffix = compartment
        else:
            compartment_suffix = compartment.split(cls.DELIMITER)[-1]
            if compartment_suffix not in cls.COMPARTMENTS:
                raise InvalidCompartmentException(f"Invalid compartment '{compartment}'")

        return compartment_suffix

    @classmethod
    def retrieve_suffix_from_compound_id(cls, compound_id):
        """ Check compartment """
        for compartment in Compartment.COMPARTMENTS:
            if compound_id.endswith(Compartment.DELIMITER + compartment):
                return compartment
        return None

    @classmethod
    def is_intracellular(cls, compartment) -> bool:
        """
        Test if the compartment is intracellular

        :return: True if the compartment is intracellular, False otherwise
        :rtype: `bool`
        """

        compartment_suffix = compartment.split(cls.DELIMITER)[-1]
        return compartment_suffix != cls.EXTRACELLULAR_SPACE and \
            compartment_suffix != cls.BIOMASS and \
            compartment_suffix != cls.SINK

    @classmethod
    def is_biomass(cls, compartment) -> bool:
        """
        Test if the compartment is the biomass compartment

        :return: True if the compartment is the biomass compartment, False otherwise
        :rtype: `bool`
        """

        compartment_suffix = compartment.split(cls.DELIMITER)[-1]
        return compartment_suffix == cls.BIOMASS

    @classmethod
    def is_sink(cls, compartment) -> bool:
        """
        Test if the compartment is a sink compartment

        :return: True if the compartment is a sink compartment, False otherwise
        :rtype: `bool`
        """

        compartment_suffix = compartment.split(cls.DELIMITER)[-1]
        return compartment_suffix == cls.SINK

    @classmethod
    def is_steady(cls, compartment) -> bool:
        """
        Test if the compartment is a steady-state compartment (is intracellular)

        :return: True if the compartment is steady, False otherwise
        :rtype: `bool`
        """

        compartment_suffix = compartment.split(cls.DELIMITER)[-1]
        return cls.COMPARTMENTS[compartment_suffix]["is_steady"]
