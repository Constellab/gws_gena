import sys

import mergem
from cobra.io import save_json_model

net1_path = sys.argv[1]
net2_path = sys.argv[2]
keep_objective = sys.argv[3]
exact_stoichiometry = sys.argv[4]
add_annotations = sys.argv[5]
use_proton = sys.argv[6]
trans_to_db = sys.argv[7]
output_path = sys.argv[8]

# Load models
model = mergem.load_model(net1_path)
model2 = mergem.load_model(net2_path)

# Merge the two models
results = mergem.merge(
    [model, model2],
    set_objective=keep_objective,
    exact_sto=exact_stoichiometry,
    use_prot=use_proton,
    extend_annot=add_annotations,
    trans_to_db=trans_to_db,
)
# retrive the merged model
merged_model = results["merged_model"]
merged_model.name = "Merged_model"
merged_model.id = "Merged_model"
# Save the merged model
save_json_model(merged_model, output_path)
