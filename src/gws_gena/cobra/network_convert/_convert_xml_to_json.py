import sys

from cobra.io import load_matlab_model, read_sbml_model, save_json_model

file_path = sys.argv[1]
output_path = sys.argv[2]

if file_path.endswith('.xml'):
    model = read_sbml_model(file_path)
elif file_path.endswith('.mat'):
    model = load_matlab_model(file_path)
else:
    raise Exception("Your file need to have a extension '.xml' or '.mat'")

save_json_model(model, output_path)
