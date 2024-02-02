# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (File,ResourceSet,OutputSpec, OutputSpecs,Logger, InputSpec, InputSpecs,task_decorator,TaskInputs,Task,
                    StrParam, TaskOutputs,ConfigParams,ListParam,Folder,ShellProxy,Table)

import os
import pandas as pd
import sys
from .pyopenms_env import PyOpenMsEnvHelper


@task_decorator("featureDetectionMetaboUntargeted", human_name="feature Detection Metabo Untargeted",
                short_description="feature Detection Metabo Untargeted.")
class featureDetectionMetaboUntargeted(Task):
    """

    This task uses pyOpenMS: an open-source Python library for mass spectrometry, specifically for the analysis of proteomics and metabolomics data in Python.
    If you want more information about this library, go here: https://pyopenms.readthedocs.io/en/latest/index.html

    Rost HL, Sachsenberg T, Aiche S, Bielow C et al. OpenMS: a flexible open-source software platform for mass spectrometry data analysis. Nat Meth. 2016; 13, 9: 741-748. doi:10.1038/nmeth.3959.

    """

    input_specs = InputSpecs({
        'mzML_file': InputSpec(File),
    })
    output_specs = OutputSpecs({
        'file_featureMap': OutputSpec(File, human_name='File featureMap', short_description='File featureMap.')
    })
    config_specs = {}

    script_features_detection_metabo_untargeted = os.path.join(os.path.abspath(os.path.dirname(__file__)),
        "_features_detection_metabo_untargeted.py")

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        mzML_file: File = inputs['mzML_file']
        file_mzml_path = mzML_file.path


        shell_proxy = PyOpenMsEnvHelper.create_proxy(self.message_dispatcher)

        output_featureMap_path = os.path.join(shell_proxy.working_dir, "test.out.featureXML")

        shell_proxy.run(f"python3 {self.script_features_detection_metabo_untargeted} {file_mzml_path} {output_featureMap_path}", shell_mode=True)


        #transform into a file
        table_featureMap = File(output_featureMap_path)

        return {'file_featureMap': table_featureMap}
