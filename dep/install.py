# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess
import shutil

__cdir__ = os.path.dirname(os.path.abspath(__file__))
EXTERNS = os.path.join(__cdir__, "../../../externs")

if __name__ == "__main__":
    
    entry_points = ["fba"]
    gena_cwd = os.path.join(EXTERNS, "gena-cpp")
    
    for point in entry_points:
        subprocess.call(
            [ "bazel", "build", f"gena:{point}" ],
            cwd = gena_cwd
        )
    
        build_path = os.path.join(__cdir__,"../bin/fba/")

        if not os.path.exists(build_path):
            os.makedirs(build_path)

        shutil.copyfile(os.path.join(gena_cwd, "bazel-bin", "gena", point), os.path.join(build_path, point))
        
        subprocess.call(
            [ "chmod", "a+x", os.path.join(build_path, point) ],
            cwd = build_path
        )