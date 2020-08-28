
python3 -m pip install --upgrade pip
python3 -m pip install virtualenv
python3 -m virtualenv .venv --python=python3

# activate vitual env
. ./.venv/bin/activate

# dependencis
python3 -m pip install -r ../biota-py/requirements.txt
python3 -m pip install -r ../gaia-py/requirements.txt

# prism requirement file
python3 -m pip install -r requirements.txt
