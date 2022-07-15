# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import BadRequestException

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
        "b": {"id": "b", "name": "biomass", "is_steady": False},
        "c": {"id": "c", "name": "cytosol", "is_steady": True},
        "cm": {"id": "cm", "name": "cytosolic membrane", "is_steady": True},
        "cx": {"id": "cx", "name": "carboxyzome", "is_steady": True},
        "e": {"id": "e", "name": "extracellular space", "is_steady": False},
        "g": {"id": "g", "name": "golgi apparatus", "is_steady": True},
        "h": {"id": "h", "name": "chloroplast", "is_steady": True},
        "f": {"id": "f", "name": "flagellum", "is_steady": True},
        "i": {"id": "i", "name": "inner mitochondrial compartment", "is_steady": True},
        "im": {"id": "im", "name": "mitochondrial intermembrane space", "is_steady": True},
        "l": {"id": "l", "name": "lysosome", "is_steady": True},
        "m": {"id": "m", "name": "mitochondria", "is_steady": True},
        "mm": {"id": "mm", "name": "mitochondria intermembrane", "is_steady": True},
        "n": {"id": "n", "name": "nucleus", "is_steady": True},
        "o": {"id": "o", "name": "other", "is_steady": True},
        "p": {"id": "p", "name": "periplasm", "is_steady": True},
        "r": {"id": "r", "name": "endoplasmic reticulum", "is_steady": True},
        "s": {"id": "s", "name": "eyespot", "is_steady": True},
        "sk": {"id": "sk", "name": "sink", "is_steady": False},
        "u": {"id": "u", "name": "thylakoid", "is_steady": True},
        "um": {"id": "um", "name": "thylakoid membrane", "is_steady": True},
        "v": {"id": "v", "name": "vacuole", "is_steady": True},
        "x": {"id": "x", "name": "peroxisome/glyoxysome", "is_steady": True},
        "y": {"id": "y", "name": "cytochrome complex", "is_steady": True},
    }

    @classmethod
    def clean(cls, data):
        """ Clean compartment data """
        replaced_compartments = {}
        compart_data = data["compartments"]
        cleaned_compart_data = {}
        for k, val in compart_data.item():

            if isinstance(val, str):
                compart_id = k
                compart_name = val
            else:
                compart_id = val["id"]
                compart_name = val["name"]

            if compart_id in cls.COMPARTMENTS:
                # ensure that "biomass" key is not used
                if compart_id == cls.BIOMASS:
                    if compart_name != cls.COMPARTMENTS[compart_id]["name"]:
                        # cannot used "biomass" key => we consider that is the "other" compartment
                        cleaned_compart_data["o"] = cls.COMPARTMENTS["o"]
                        replaced_compartments[k] = "o"
                    else:
                        cleaned_compart_data[k] = cls.COMPARTMENTS[k]
                else:
                    cleaned_compart_data[k] = cls.COMPARTMENTS[k]
            else:
                # we consider that it is the "other" compartment
                cleaned_compart_data["o"] = cls.COMPARTMENTS["o"]
                replaced_compartments[k] = "o"

        data["compartments"] = cleaned_compart_data
        replaced_met = {}

        if replaced_compartments:
            for i, met in enumerate(data["metabolites"]):
                old_compart = met["compartment"]
                if old_compart in replaced_compartments:
                    new_compart = replaced_compartments[old_compart]
                    old_id = met["id"]
                    new_id = "_".join(met["id"].split("_")[:-1]) + "_" + new_compart

                    met["compartment"] = new_compart
                    met["id"] = new_id
                    replaced_met[old_id] = new_id

                    data["metabolites"][i] = met

        if replaced_met:
            for i, rxn in enumerate(data["reactions"]):
                new_rxn_nets = {}
                for name in rxn["metabolites"]:
                    if name in replaced_met:
                        new_name = replaced_met[name]
                        new_rxn_nets[new_name] = rxn["metabolites"][name]
                    else:
                        new_rxn_nets[name] = rxn["metabolites"][name]

                data["reactions"][i]["metabolites"] = new_rxn_nets

        return data

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
