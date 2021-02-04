import os
import subprocess

__cdir__ = os.path.dirname(os.path.abspath(__file__))
EXTERNS = os.path.join(__cdir__, "../../externs")

if __name__ == "__main__":
    
    subprocess.call(
        [ "bazel", "build", "gena:main" ],
        cwd = os.path.join(EXTERNS, "gena-cpp")
    )

    
    