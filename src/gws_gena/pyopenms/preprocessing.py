# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (File,ResourceSet,OutputSpec, OutputSpecs,Logger, InputSpec, InputSpecs,task_decorator,TaskInputs,Task,
                    StrParam, TaskOutputs,ConfigParams,ListParam,Folder,ShellProxy)

import os
import pandas as pd
import sys
import pyopenms as oms
import json


@task_decorator("mzMLPreprocessing", human_name="mzML Preprocessing",
                short_description="Preprocess mzML files.")
class mzMLPreprocessing(Task):
    """
    Task to preprocess a mzML file.



    This task uses pyOpenMS: an open-source Python library for mass spectrometry, specifically for the analysis of proteomics and metabolomics data in Python.
    If you want more information about this library, go here: https://pyopenms.readthedocs.io/en/latest/index.html

    Rost HL, Sachsenberg T, Aiche S, Bielow C et al. OpenMS: a flexible open-source software platform for mass spectrometry data analysis. Nat Meth. 2016; 13, 9: 741-748. doi:10.1038/nmeth.3959.

    """

    input_specs = InputSpecs({
        'mzML_file': InputSpec(File),
    })
    output_specs = OutputSpecs({
        'summary_table': OutputSpec(File, human_name='Summary', short_description='Summary of the mzML file.'),
        'mzMLfile_modified' : OutputSpec(File, human_name='mzMLfile modified', short_description='mzMLfile_modified')
    })
    config_specs = {
        "smoothing": StrParam(
            default_value="No", allowed_values=["No","Yes"],
            human_name="Smoothing", short_description="Does the file need to be smooth?"),
        "centroiding": StrParam(
            default_value="No", allowed_values=["No","Yes"],
            human_name="Centroiding", short_description="Does the file need to be centred?"),
        "normalisation": StrParam(
            default_value="No", allowed_values=["No","Yes, to one","Yes, Total Ion Count (TIC) normalisation"],
            human_name="Normalisation", short_description="Does the file need to be normalised? If so, which one?")
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        mzML_file: File = inputs['mzML_file']
        smoothing = params['smoothing']
        centroiding = params['centroiding']
        normalisation = params['normalisation']

        #Create experiment
        exp = oms.MSExperiment()

        #Call smoothing function: smoothes if necessary, either load data only
        exp = self.smoothing(smoothing,exp, mzML_file)

        #Call centroiding function:
        if centroiding == "Yes":
            exp = self.centroiding(exp)

        #Call normalisation function:
        if normalisation.startswith("Yes"):
            exp = self.normalisation_function(exp,normalisation)

        #Create the JSON file that summarises some useful information
        summary_json = self.create_summary_json(exp)


        #save the file modified
        path_mzml_file_modified = os.path.join(os.path.abspath(os.path.dirname(__file__)), "mzMLfile_modified.mzML")
        oms.MzMLFile().store(path_mzml_file_modified, exp)
        mzMLfile_modified = File(path_mzml_file_modified)

        return {'summary_table': summary_json,"mzMLfile_modified" : mzMLfile_modified}

    def centroiding(self, exp):
        centroided_spectra = oms.MSExperiment()
        # input, output, chec_spectrum_type (if set, checks spectrum type and throws an exception if a centroided spectrum is passed)
        oms.PeakPickerHiRes().pickExperiment(exp, centroided_spectra)  # pick all spectra
        centroided_spectra.updateRanges()

        return centroided_spectra


    def create_summary_json(self,exp):
        ms_levels = exp.getMSLevels()
        num_spectra = {level: 0 for level in ms_levels}

        for spec in exp:
            num_spectra[spec.getMSLevel()] += 1

        # Create a dictionary to store the output data
        summary_json = {}
        # Instrument information
        summary_json["Instrument"] = []
        for analyzer in exp.getInstrument().getMassAnalyzers():
            summary_json["Instrument"].append({
                "Mass Analyzer": analyzer.getType(),
                "Resolution": analyzer.getResolution()
            })
        # Other information
        summary_json["MS_levels"] = ms_levels
        summary_json["Total_number_of_peaks"] = sum([spec.size() for spec in exp])
        summary_json["Total_number_of_spectra"] = exp.getNrSpectra()
        summary_json["Total_number_of_chromatograms"] = exp.getNrChromatograms()

        summary_json["Ranges"] = {
            "retention_time": f"{exp.getMinRT()} to {exp.getMaxRT()} ({round((exp.getMaxRT()-exp.getMinRT())/60, 2)} min)",
            "mass_to_charge": f"{exp.getMinMZ()} to {exp.getMaxMZ()}",
            "intensity": f"{exp.getMinInt()} to {exp.getMaxInt()}"
        }

        summary_json["Number_of_spectra_per_MS_level"] = num_spectra

        # Write the data to a JSON file
        with open("summary_table.json", "w") as json_file:
            json.dump(summary_json, json_file, indent=4)

        summary_json = File('summary_table.json')

        return summary_json

    def normalisation_function(self, exp, normalisation):
        normalizer = oms.Normalizer()
        param = normalizer.getParameters()
        if (normalisation == "Yes, to one"):
            param.setValue("method", "to_one")
        elif (normalisation == "Yes, Total Ion Count (TIC) normalisation"):
            param.setValue("method", "to_TIC")

        normalizer.setParameters(param)
        normalizer.filterPeakMap(exp)
        exp.updateRanges()

        return exp

    def smoothing(self, smoothing, exp, mzML_file):
        if (smoothing == "Yes"):
            gf = oms.GaussFilter()
            param = gf.getParameters()
            param.setValue("gaussian_width", 1.0)  # needs wider width
            gf.setParameters(param)

            oms.MzMLFile().load(mzML_file.path, exp)
            gf.filterExperiment(exp)
            #oms.MzMLFile().store("file.smoothed.mzML", exp) #TODO : voir si il faut garder le fichier et peut être le renvoyer à l'user?
        else:
            #Load data from mzML file
            oms.MzMLFile().load(mzML_file.path, exp)

        #The range values (min, max, etc.) are not updated automatically. Call updateRanges() to update the values!
        exp.updateRanges()

        return exp
