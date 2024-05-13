
from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, Table, Task, TaskInputs, TaskOutputs,
                      TypingStyle, task_decorator, ConfigSpecs,IntParam,StrParam, FloatParam, File)
import pandas as pd
import numpy as np

@task_decorator("GenerationMultiSimulations", human_name="Generation Multi Simulations",
                short_description="Build a Table with multi simulations context for a metabolic network using a flux table",
                style=TypingStyle.material_icon(material_icon_name="library_add", background_color="#d9d9d9"))
class GenerationMultiSimulations(Task):
    """
    GenerationMultiSimulations Task

    This task allows you to generate data simulations to contextualise a digital twin.

    Please provide a table or a file with your replicate data as follows:
    ,replicat1,replicat2,replicat3
    chemical,2,1.5,3.5
    chemical,23,21.23,22.02

    Chemicals must be indexed.

    You can use this task to generate data simulations for reactions or metabolites.
    We recommend that you separate these chemical types into two different tables if you have both.

    The output can then be used to build a context with the "Context builder" Task.

    """

    input_specs = InputSpecs({
        'experimental_data': InputSpec((Table, File), human_name="Experimental data")})
    output_specs = OutputSpecs({'simulations': OutputSpec(Table)})
    config_specs: ConfigSpecs = {
        'number_simulations': IntParam(human_name="Number of simulations", min_value=1,short_description="Number of simulations to generate"),
        'type_generation': StrParam(human_name="Distribution generation",
           short_description="Law to follow to generate simulated data from your data distribution",
           allowed_values = ["Multivariate normal distribution", "Normal distribution"]),
        "confidence_score":FloatParam(
            default_value=1.0, min_value=0.0, max_value=1.0, visibility=StrParam.PROTECTED_VISIBILITY,
            human_name="Confidence score",
            short_description="Confidence score")
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        experimental_data = inputs["experimental_data"]
        if isinstance(experimental_data, Table):
            experimental_data = experimental_data.get_data()
        elif isinstance(experimental_data, File):
            experimental_data: File = inputs['experimental_data']
            experimental_data = pd.read_csv(experimental_data.path, header=0, index_col=0, sep=',')

        number_simulations = params["number_simulations"]
        type_generation = params["type_generation"]
        confidence_score_value = params["confidence_score"]

        simulated_data = self.create_simulated_data(number_simulations= number_simulations, experimental_data=experimental_data, type_generation = type_generation)

        #Convert MultiIndex to Index
        new_index = simulated_data.index.get_level_values(0)
        # Replace the DataFrame's index with the new single-level Index
        simulated_data = simulated_data.set_index(new_index)
        # Drop the old MultiIndex level
        simulated_data.index.name = None

        #Generate data
        simulations_generated = self.generation_simulations_context(context = simulated_data, number_simulations=number_simulations, confidence_score_value = confidence_score_value)

        return {"simulations": simulations_generated}


    def create_simulated_data(self, number_simulations: int, experimental_data: pd.DataFrame, type_generation : str) -> pd.DataFrame:
        if type_generation == "Multivariate normal distribution":
            #Compute the mean of the replicates
            mean_vector = np.mean(experimental_data, axis=1)
            #Compute the covariance matrix
            covariance_matrix = np.cov(experimental_data, rowvar=True)
            #Generate random numbers from the mean and the covariance
            matrix_generated = np.random.multivariate_normal(mean_vector,covariance_matrix, number_simulations)
        elif type_generation == "Normal distribution":
            #Compute the mean of the replicates
            mean_vector = np.mean(experimental_data, axis=1)
            #Compute the standard deviation
            std = np.std(experimental_data,axis=1)
            #Generate random numbers from the mean and the covariance
            matrix_generated = np.random.normal(mean_vector,std, (number_simulations,len(experimental_data)))
        #Add them into a dataframe
        matrix_generated = pd.DataFrame(matrix_generated)
        matrix_generated.columns = [experimental_data.index]
        matrix_generated=matrix_generated.transpose()

        #transform all the columns into one vector in a new dataframe
        data_sim_2 = pd.DataFrame({'target': matrix_generated.apply(lambda row: row.values, axis=1).tolist()})
        data_sim_2.index = [experimental_data.index]

        return data_sim_2

    def generation_simulations_context(self, context: pd.DataFrame, number_simulations: int, confidence_score_value : float) -> Table:
        #We will put a value of lower/upper bound depending of the value of the standard deviation
        # Calculate the standard deviation for each row
        context['std_dev'] = context["target"].apply(lambda x: np.std(x))
        # Add a new column with the vector of each value + each standard deviation
        context["lower_bound"] = context.apply(lambda row: [value - row['std_dev'] for value in row["target"]], axis=1)
        context["upper_bound"] = context.apply(lambda row: [value + row['std_dev'] for value in row["target"]], axis=1)
        context.drop(columns=['std_dev'], inplace=True)

        #Add the confidence score
        context["confidence_score"] = 0
        new_vector = [confidence_score_value] * number_simulations
        context["confidence_score"] = context["confidence_score"].apply(lambda x: new_vector)

        #Convert the vector target directly into str with comma as separators and other columns to the right format
        context["target"] = context["target"].apply(lambda x: np.array2string(x, separator=', '))
        context["confidence_score"] = np.array([np.array2string(np.array(xi), separator=', ') for xi in context["confidence_score"]])
        context["lower_bound"] = np.array([np.array2string(np.array(xi), separator=', ') for xi in context["lower_bound"]])
        context["upper_bound"] = np.array([np.array2string(np.array(xi), separator=', ') for xi in context["upper_bound"]])

        #Delete index and create id column
        context.reset_index(inplace=True)
        context.rename(columns={'index': 'id'}, inplace=True)

        #Transform into Table
        context = Table(context)

        return context
