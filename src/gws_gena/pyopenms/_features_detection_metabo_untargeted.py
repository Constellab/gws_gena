from gws_core import (File,ResourceSet,OutputSpec, OutputSpecs,Logger, InputSpec, InputSpecs,task_decorator,TaskInputs,Task,
    StrParam, TaskOutputs,ConfigParams,ListParam,Folder,ShellProxy,Table)

import os
import pandas as pd
import sys
import pyopenms as oms
import json


file_mzml_path = sys.argv[1]
output_featureMap_path = sys.argv[2]


#Create experiment
exp = oms.MSExperiment()
oms.MzMLFile().load(file_mzml_path, exp)

exp.sortSpectra(True)

#Mass trace detection
mass_traces = []
mtd = oms.MassTraceDetection()
mtd_params = mtd.getDefaults()
mtd_params.setValue("mass_error_ppm", 5.0)  # set according to your instrument mass error
mtd_params.setValue("noise_threshold_int", 3000.0) # adjust to noise level in your data
mtd.setParameters(mtd_params)
mtd.run(exp, mass_traces, 0)

mass_traces_split = []
mass_traces_final = []

#Elution peak detection
epd = oms.ElutionPeakDetection()
epd_params = epd.getDefaults()
epd_params.setValue("width_filtering", "fixed")
epd.setParameters(epd_params)
epd.detectPeaks(mass_traces, mass_traces_split)

if epd.getParameters().getValue("width_filtering") == "auto":
    epd.filterByPeakWidth(mass_traces_split, mass_traces_final)
else:
    mass_traces_final = mass_traces_split

fm = oms.FeatureMap()
feat_chrom = []
ffm = oms.FeatureFindingMetabo()
ffm_params = ffm.getDefaults()
ffm_params.setValue("isotope_filtering_model", "none")
ffm_params.setValue(
    "remove_single_traces", "true"
)  # set false to keep features with only one mass trace
ffm_params.setValue("mz_scoring_by_elements", "false")
ffm_params.setValue("report_convex_hulls", "true")
ffm.setParameters(ffm_params)
ffm.run(mass_traces_final, fm, feat_chrom)

fm.setUniqueIds()
fm.setPrimaryMSRunPath(["ms_data.mzML".encode()])

#get dataframe
#dataframe_featureMap = fm.get_df()
fm.size() #get the lenght of features found

oms.FeatureXMLFile().store(output_featureMap_path, fm)