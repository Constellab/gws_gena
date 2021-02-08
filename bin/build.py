# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess
from shutil import copyfile

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

        build_path = os.path.join(__cdir__,"./build/")

        if not os.path.exists(build_path):
            os.makedirs(build_path)

        copyfile(os.path.join(gena_cwd, "bazel-bin", "gena", point), os.path.join(build_path, point))