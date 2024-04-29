
import math
import ast

from gws_core import (BadRequestException,Table)

from ...network.reaction.reaction import Reaction
from ...network.compound.compound import Compound
from ..context import Context
from ..measure import Measure
from ..typing.measure_typing import MeasureDict
from ..typing.variable_typing import VariableDict
from ...helper.base_helper import BaseHelper
from ...data.task.transformer_phenotype_table import TransformerPhenotypeTable
from ...data.task.transformer_flux_table import TransformerFluxTable


class ContextBuilderHelper(BaseHelper):
    """
    ContextBuilderHelper

    This helper creates a `Context` object using a `Flux Table` and metabolic `Network`.
    A `Context` object is used to create digital twins and perform metabolic flux analyses.

    - The `flux_table` gives a list of metabolic fluxes experimentally measured.
    - The `met_table` gives a list of metabolic fluxes experimentally measured.
    It generally corresponds to the consupmtion or production rates of a list on metabolites measured in a bioreactor.
    - The `Network` is a metabolic network
    """

    def build(self, net, flux_table: Table, pheno_table: Table) -> Context:
        ctx = Context()
        if (flux_table is None) and (pheno_table is None):
            return ctx

        entity_id_column_name = TransformerPhenotypeTable.entity_id_column_name
        target_column_name = TransformerPhenotypeTable.target_column_name
        lower_bound_column_name = TransformerPhenotypeTable.lower_bound_column_name
        upper_bound_column_name = TransformerPhenotypeTable.upper_bound_column_name
        confidence_score_column = TransformerPhenotypeTable.confidence_score_column

        #Test if the table for phenotype table has the right column names
        if pheno_table :
            if not pheno_table.column_exists(entity_id_column_name):
                raise Exception(f"Cannot import Phenotype Table: no column with name '{entity_id_column_name}' found, use the Transformer Phenotype Table")
            if not pheno_table.column_exists(target_column_name):
                raise Exception(f"Cannot import Phenotype Table: no column with name '{target_column_name}', use the Transformer Phenotype Table")
            if not pheno_table.column_exists(upper_bound_column_name):
                raise Exception(f"Cannot import Phenotype Table: no column with name '{upper_bound_column_name}', use the Transformer Phenotype Table")
            if not pheno_table.column_exists(lower_bound_column_name):
                raise Exception(f"Cannot import Phenotype Table: no column with name '{lower_bound_column_name}', use the Transformer Phenotype Table")
            if not pheno_table.column_exists(confidence_score_column):
                raise Exception(f"Cannot import Phenotype Table: no column with name '{confidence_score_column}', use the Transformer Phenotype Table")

        flux_table_entity_id_column_name = TransformerFluxTable.entity_id_column_name
        flux_table_target_column_name = TransformerFluxTable.target_column_name
        flux_table_lower_bound_column_name = TransformerFluxTable.lower_bound_column_name
        flux_table_upper_bound_column_name = TransformerFluxTable.upper_bound_column_name
        flux_table_confidence_score_column = TransformerFluxTable.confidence_score_column
        #Test if the table for flux_table has the right column names
        if flux_table :
            if not flux_table.column_exists(flux_table_entity_id_column_name):
                raise Exception(f"Cannot import Flux Table: no column with name '{flux_table_entity_id_column_name}' found, use the Transformer Flux Table")
            if not flux_table.column_exists(flux_table_target_column_name):
                raise Exception(f"Cannot import Flux Table: no column with name '{flux_table_target_column_name}', use the Transformer Flux Table")
            if not flux_table.column_exists(flux_table_upper_bound_column_name):
                raise Exception(f"Cannot import Flux Table: no column with name '{flux_table_upper_bound_column_name}', use the Transformer Flux Table")
            if not flux_table.column_exists(flux_table_lower_bound_column_name):
                raise Exception(f"Cannot import Flux Table: no column with name '{flux_table_lower_bound_column_name}', use the Transformer Flux Table")
            if not flux_table.column_exists(flux_table_confidence_score_column):
                raise Exception(f"Cannot import Flux Table: no column with name '{flux_table_confidence_score_column}', use the Transformer Flux Table")


        all_tables = {'rxn': flux_table, 'met': pheno_table}

        def are_all_lists_equal_length(list_of_lists):
            # Check if all lists have the same length
            return all(len(lst) == len(list_of_lists[0]) for lst in list_of_lists)

        def are_all_values_float_or_int(list_of_lists):
            # Check if all values are float or int
            if isinstance(list_of_lists[0], (float, int)):
                # If it's a single list, check each value in that list
                return all(isinstance(value, (float, int)) for value in list_of_lists)
            else:
                # If it's a list of lists, check each value in all lists
                return all(isinstance(value, (float, int)) for lst in list_of_lists for value in lst)

        for key, table in all_tables.items():
            if table is None:
                continue

            targets = table.get_column_data(target_column_name)
            ubounds = table.get_column_data(upper_bound_column_name)
            lbounds = table.get_column_data(lower_bound_column_name)
            scores = table.get_column_data(confidence_score_column)

            if key == "rxn":
                ids = table.get_column_data(flux_table_entity_id_column_name)
                data = net.reactions
            else:
                ids = table.get_column_data(entity_id_column_name)
                data = net.compounds

            if isinstance(targets[0], str):  # if there is multiple simulations
                for i in range(0, len(targets)):
                    targets[i] = ast.literal_eval(targets[i])
                    ubounds[i] = ast.literal_eval(ubounds[i])
                    lbounds[i] = ast.literal_eval(lbounds[i])
                    scores[i] = ast.literal_eval(scores[i])
                # test if we have the same number of simulations
                if not are_all_lists_equal_length(targets):
                    raise BadRequestException("All simulations for target value must have the same length.")
                if not are_all_lists_equal_length(ubounds):
                    raise BadRequestException("All simulations for ubounds value must have the same length.")
                if not are_all_lists_equal_length(lbounds):
                    raise BadRequestException("All simulations for lbounds value must have the same length.")
                if not are_all_lists_equal_length(scores):
                    raise BadRequestException("All simulations for scores value must have the same length.")
                # test if all values of simulations are int or float
                if not are_all_values_float_or_int(targets):
                    raise BadRequestException("All values for target value must be a int or float.")
                if not are_all_values_float_or_int(ubounds):
                    raise BadRequestException("All values for ubounds value must be a int or float.")
                if not are_all_values_float_or_int(lbounds):
                    raise BadRequestException("All values for lbounds value must be a int or float.")
                if not are_all_values_float_or_int(scores):
                    raise BadRequestException("All values for scores value must be a int or float.")

                for i, ref_id in enumerate(ids):
                    if ref_id in data:
                        for j in range(0, len(ubounds[i])):
                            if ubounds[i][j] < lbounds[i][j]:
                                raise BadRequestException(f"Flux {ref_id} for the simulation {j}: the upper bound must be greater than lower bound")
                            if targets[i][j] < lbounds[i][j]:
                                raise BadRequestException(f"Flux {ref_id} for the simulation {j}: the target must be greater than lower bound")
                            if targets[i][j] > ubounds[i][j]:
                                raise BadRequestException(f"Flux {ref_id} for the simulation {j}: the target must be smaller than upper bound")

                        lbound = lbounds[i]
                        ubound = ubounds[i]
                        if key == "rxn":
                            lbound = [Reaction.LOWER_BOUND if math.isnan(x) else x for x in lbound]
                            ubound = [Reaction.UPPER_BOUND if math.isnan(x) else x for x in ubound]
                        else:
                            lbound = [Compound.LOWER_BOUND if math.isnan(x) else x for x in lbound]
                            ubound = [Compound.UPPER_BOUND if math.isnan(x) else x for x in ubound]

                        score = scores[i]
                        score = [1.0 if math.isnan(x) else x for x in score]

                        target = targets[i]
                        for value in target :
                            if isinstance(data[ref_id],Reaction):
                                #test if one target is not in the range of the value of the network
                                if value > data[ref_id].upper_bound or value < data[ref_id].lower_bound :
                                    #raises a warning
                                    self.log_warning_message(f'The value {value} is not within the range of the reaction {ref_id} in the network. In the network, the range is [{data[ref_id].lower_bound} : {data[ref_id].upper_bound}]')
                            elif isinstance(data[ref_id],Compound):
                                #test if one target is not in the range of the value of the network
                                if value > data[ref_id].UPPER_BOUND or value < data[ref_id].LOWER_BOUND :
                                    #raises a warning
                                    self.log_warning_message(f'The value {value} is not within the range of the reaction {ref_id} in the network. In the network, the range is [{data[ref_id].lower_bound} : {data[ref_id].upper_bound}]')

                        for i in range(len(target)):
                            if math.isnan(target[i]):
                                target[i] = 0.0
                                score[i] = 0.0  # set the output confidence score to zero if it is NaN

                        measure = Measure(
                            MeasureDict(
                                id=f"{key}_" + ref_id,
                                name = None,
                                target=target,
                                upper_bound=ubound,
                                lower_bound=lbound,
                                confidence_score=score,
                                variables=[
                                    VariableDict(
                                        coefficient=1.0,
                                        reference_id=ref_id,
                                    )]
                            ))
                        if key == "rxn":
                            ctx.add_reaction_data(measure)
                        else:
                            ctx.add_compound_data(measure)
                    else:
                        raise Exception(f"No reference reaction or metabolite found with id {ref_id}")

            elif (isinstance(targets[0], (float, int))):  # if there is only one simulation
                # test if all values are int or float
                if not are_all_values_float_or_int(targets):
                    raise BadRequestException("All values for target value must be a int or float.")
                if not are_all_values_float_or_int(ubounds):
                    raise BadRequestException("All values for ubounds value must be a int or float.")
                if not are_all_values_float_or_int(lbounds):
                    raise BadRequestException("All values for lbounds value must be a int or float.")
                if not are_all_values_float_or_int(scores):
                    raise BadRequestException("All values for scores value must be a int or float.")

                for i, ref_id in enumerate(ids):
                    if ref_id in data:
                        if ubounds[i] < lbounds[i]:
                            raise BadRequestException(f"Flux {ref_id}: the upper bound must be greater than lower bound")
                        if targets[i] < lbounds[i]:
                            raise BadRequestException(f"Flux {ref_id}: the target must be greater than lower bound")
                        if targets[i] > ubounds[i]:
                            raise BadRequestException(f"Flux {ref_id}: the target must be smaller than upper bound")

                        if key == "rxn":
                            lbound = Reaction.LOWER_BOUND if math.isnan(lbounds[i]) else lbounds[i]
                            ubound = Reaction.UPPER_BOUND if math.isnan(ubounds[i]) else ubounds[i]
                        else :
                            lbound = Compound.LOWER_BOUND if math.isnan(lbounds[i]) else lbounds[i]
                            ubound = Compound.UPPER_BOUND if math.isnan(ubounds[i]) else ubounds[i]

                        lbound = [lbound]
                        ubound = [ubound]

                        score = 1.0 if math.isnan(scores[i]) else scores[i]
                        score = [score]

                        if math.isnan(targets[i]):
                            targets[i] = 0.0
                            score = [0.0]  # set the output confidence score to zero if it is NaN

                        target = [targets[i]]
                        #test if the target is not in the range of the value of the network
                        if isinstance(data[ref_id],Reaction):
                            if target[0] > data[ref_id].upper_bound or target[0] < data[ref_id].lower_bound :
                                #raises a warning
                                self.log_warning_message(f'The value {target[0]} is not within the range of the reaction {ref_id} in the network. In the network, the range is [{data[ref_id].lower_bound} : {data[ref_id].upper_bound}]')
                        elif isinstance(data[ref_id],Compound):
                            if target[0] > data[ref_id].UPPER_BOUND or target[0] < data[ref_id].LOWER_BOUND :
                                #raises a warning
                                self.log_warning_message(f'The value {target[0]} is not within the range of the reaction {ref_id} in the network. In the network, the range is [{data[ref_id].lower_bound} : {data[ref_id].upper_bound}]')

                        measure = Measure(
                            MeasureDict(
                                id=f"{key}_" + ref_id,
                                name = None,
                                target=target,
                                upper_bound=ubound,
                                lower_bound=lbound,
                                confidence_score=score,
                                variables=[
                                    VariableDict(
                                        coefficient=1.0,
                                        reference_id=ref_id,
                                    )]
                            ))
                        if key == "rxn":
                            ctx.add_reaction_data(measure)
                        else:
                            ctx.add_compound_data(measure)
                    else:
                        raise Exception(f"No reference reaction or metabolite found with id {ref_id}")

            else:
                raise Exception(
                    "The target values are not of the correct type. We expected float, int or string. Strings store lists of simulations")

        return ctx

    # Method to build a sub context of a big context.
    # Useful for example if we have multiples measures for one reaction (case of multi simulations; see FBA)
    def build_sub_context(self, base_context: Context, index: int) -> Context:
        ctx = Context()

        data = ["reaction_data", "compound_data"]

        for elt in data:
            dict_ = getattr(base_context, elt)
            for measure_id, measure in dict_.items():  # run through the number of context measures
                value_target = measure.target[index]
                value_upper = measure.upper_bound[index]
                value_lower = measure.lower_bound[index]
                value_confidence_score = measure.confidence_score[index]
                # Create a new measure
                measure = Measure(
                    MeasureDict(
                        id=measure_id,
                        name = None,
                        target=value_target,
                        upper_bound=value_upper,
                        lower_bound=value_lower,
                        confidence_score=value_confidence_score,
                        variables=[
                            VariableDict(
                                coefficient=1.0,
                                reference_id=measure.variables[0].reference_id,
                            )]
                    ))
                if elt == "reaction_data":
                    ctx.add_reaction_data(measure)
                else:
                    ctx.add_compound_data(measure)

        return ctx
