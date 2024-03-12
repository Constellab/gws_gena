import re
import csv
from gws_core import (task_decorator, Task, OutputSpec, OutputSpecs, Folder,
                      ConfigParams, StrParam, TaskInputs, TaskOutputs, Settings, FileDownloader)

@task_decorator("TransformMetabolitesFile", human_name="Metabolites file transformation",
                short_description="Transformation of the Bigg Models database metabolites file", hide = True)
class TransformMetabolitesFile(Task):
    output_specs = OutputSpecs({"output": OutputSpec(Folder, human_name="Output folder",
                                                     short_description="transformed metabolites file")})
    config_specs = {"URL": StrParam(default_value="http://bigg.ucsd.edu/static/namespace/bigg_models_metabolites.txt",
                                    human_name="File URL", short_description="URL of the metabolites.txt file to download")}
    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        destination_dir = Settings.make_temp_dir()
        file_downloader = FileDownloader(destination_dir)
        metabolites_file = file_downloader.download_file_if_missing(params["URL"], filename="metabolites.txt")
        metabolites_dict = {}
        #Check if there is a chebi id in the line and create a dictionary if there is.
        with open(metabolites_file, "r", encoding='utf-8') as file:
            for line in file:
                if "chebi" in line:
                    line_info = line.split()
                    bigg = line_info[1]
                    name = line_info[2]
                    chebi_id = "CHEBI:" + re.findall(r"chebi\/CHEBI:([0-9]+)", line)[0]
                    metabolites_dict[bigg] = {"name": name, "chebi": chebi_id}
        #Write the csv output
        header = ['BIGG', 'Name', 'CHEBI']
        with open(f"{destination_dir}/restructured_metabolites_file.txt", "w", encoding='utf-8') as new_file:
            writer = csv.DictWriter(new_file, fieldnames=header, delimiter='\t')
            # Write the header
            writer.writeheader()
            # Write the dictionary
            for key, value in metabolites_dict.items():
                writer.writerow({'BIGG': key , 'Name': value['name'], 'CHEBI': value['chebi']})
        return {"output": Folder(destination_dir)}


@task_decorator("TransformReactionsFile", human_name="Reactions file transformation",
                 short_description="Transformation of the Bigg Models database reactions file", hide = True)
class TransformReactionsFile(Task):
    output_specs = OutputSpecs({"output": OutputSpec(Folder, human_name="Output folder",
                                                     short_description="transformed reactions file")})
    config_specs = {"URL": StrParam(default_value="http://bigg.ucsd.edu/static/namespace/bigg_models_reactions.txt",
                                    human_name="File URL", short_description="URL of the reactions.txt file to download")}
    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        destination_dir = Settings.make_temp_dir()
        file_downloader = FileDownloader(destination_dir)
        reactions_file = file_downloader.download_file_if_missing(params["URL"], filename="reactions.txt")
        reactions_dict = {}
        with open(reactions_file, "r", encoding='utf-8') as file:
            for line in file:
                self.log_info_message(line.split()[0])
                #Check if there is a RHEA and/or EC number in the line and create a dictionary if there is.
                if "rhea" in line:
                    bigg_id = line.split()[0]
                    rhea_id = re.findall(r"rhea\/([0-9]+)", line)[0]
                    if "ec-code" in line:
                        ec_number = re.findall(r"ec-code\/(\d+(?:\.\d+)*)", line)[0]
                    else:
                        ec_number = ""
                    reactions_dict[bigg_id] ={"rhea": str(rhea_id), "ec_number": ec_number}
                elif "ec-code" in line:
                    bigg_id = line.split()[0]
                    ec_number = re.findall(r"ec-code\/(\d+(?:\.\d+)*)", line)[0]
                    if "rhea" in line:
                        rhea_id = re.findall(r"rhea\/([0-9]+)", line)[0]
                    else:
                        rhea_id = ""
                    reactions_dict[bigg_id] ={"rhea": str(rhea_id), "ec_number": ec_number}
        #Write the csv output
        header = ['BIGG', 'RHEA', 'EC-number']
        with open(f"{destination_dir}/restructured_reactions_file.txt", "w", encoding='utf-8') as restructured_file:
            writer = csv.DictWriter(restructured_file, fieldnames=header, delimiter='\t')
            # Write the header
            writer.writeheader()
            # Write the dictionary
            for key, value in reactions_dict.items():
                writer.writerow({'BIGG': key , 'RHEA': value['rhea'], 'EC-number': value['ec_number']})
        return {"output": Folder(destination_dir)}
