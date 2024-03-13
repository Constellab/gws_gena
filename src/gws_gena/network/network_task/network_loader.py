import os
import pandas as pd
from gws_core import (task_decorator, Task, OutputSpec, OutputSpecs, File,
                      ConfigParams, StrParam, TaskInputs, TaskOutputs,TypingStyle)

@task_decorator("LoadBiggModels", human_name="Load BiGG Models",
                short_description="Retrieve data from Bigg Models database",
                style=TypingStyle.material_icon(material_icon_name="travel_explore", background_color="#089bcc"))
class LoadBiGGModels(Task):
    """
    This task allows you to retrieve a metabolic model from the BiGG database.
    In the parameters you must specify the organism identifier from the Bigg Models database. For example, iMM1415 for "mus musculus".
    You can also select the output file format (json recommended).
    """
    output_specs = OutputSpecs({"output": OutputSpec(File, human_name="Output file",
                               short_description="File containing desired model")})
    config_specs = {
        "organism": StrParam(human_name="Bigg Models id",
            short_description="Bigg Models database organism identifier", default_value="", optional = True),
        "name_organism" : StrParam(human_name="Bigg Models name",
           short_description="Bigg Models database organism name", optional = True,
           allowed_values = ["Acinetobacter baumannii AYE","Bacillus subtilis subsp. subtilis str. 168","Chlamydomonas reinhardtii","Clostridioides difficile 630","Clostridium ljungdahlii DSM 13528","Cricetulus griseus, iCHOv1","Cricetulus griseus, iCHOv1_DG44","Escherichia coli 042","Escherichia coli 536","Escherichia coli 55989","Escherichia coli ABU 83972","Escherichia coli APEC O1","Escherichia coli ATCC 8739","Escherichia coli ATCC 8739, iEC1349_Crooks","Escherichia coli B str. REL606","Escherichia coli BL21(DE3)","Escherichia coli BL21(DE3), iB21_1397","Escherichia coli BL21(DE3), iEC1356_Bl21DE3","Escherichia coli 'BL21-Gold(DE3)pLysS AG'","Escherichia coli BW2952","Escherichia coli C","Escherichia coli CFT073","Escherichia coli DH1, iEcDH1_1363","Escherichia coli DH1, iECDH1ME8569_1439","Escherichia coli DH5[alpha]","Escherichia coli ED1a","Escherichia coli ETEC H10407","Escherichia coli HS","Escherichia coli IAI1","Escherichia coli IAI39","Escherichia coli IHE3034","Escherichia coli KO11FL","Escherichia coli LF82","Escherichia coli NA114","Escherichia coli O103:H2 str. 12009","Escherichia coli O111:H- str. 11128","Escherichia coli O127:H6 str. E2348/69","Escherichia coli O139:H28 str. E24377A","Escherichia coli O157:H7 str. EC4115","Escherichia coli O157:H7 str. EDL933","Escherichia coli O157:H7 str. Sakai","Escherichia coli O157:H7 str. TW14359","Escherichia coli O26:H11 str. 11368","Escherichia coli O55:H7 str. CB9615","Escherichia coli O83:H1 str. NRG 857C","Escherichia coli S88","Escherichia coli SE11","Escherichia coli SE15","Escherichia coli SMS-3-5","Escherichia coli str. K-12 substr. DH10B","Escherichia coli str. K-12 substr. MG1655, e_coli_core","Escherichia coli str. K-12 substr. MG1655, iAF1260","Escherichia coli str. K-12 substr. MG1655, iAF1260b","Escherichia coli str. K-12 substr. MG1655, iJO1366","Escherichia coli str. K-12 substr. MG1655, iJR904","Escherichia coli str. K-12 substr. MG1655, iML1515","Escherichia coli str. K-12 substr. W3110","Escherichia coli str. K-12 substr. W3110, iEC1372_W3110","Escherichia coli UM146","Escherichia coli UMN026","Escherichia coli UMNK88","Escherichia coli UTI89","Escherichia coli W","Escherichia coli W, iEC1364_W","Escherichia coli W, iWFL_1372","Geobacter metallireducens GS-15","Helicobacter pylori 26695","Homo sapiens, iAB_RBC_283","Homo sapiens, iAT_PLT_636","Homo sapiens, RECON1","Homo sapiens, Recon3D","Klebsiella pneumoniae subsp. pneumoniae MGH 78578","Lactococcus lactis subsp. cremoris MG1363","Methanosarcina barkeri str. Fusaro","Mus musculus","Mycobacterium tuberculosis H37Rv","Mycobacterium tuberculosis H37Rv, iNJ661","Organism","Phaeodactylum tricornutum CCAP 1055/1","Plasmodium berghei","Plasmodium cynomolgi strain B","Plasmodium falciparum 3D7","Plasmodium knowlesi strain H","Plasmodium vivax Sal-1","Pseudomonas putida KT2440, iJN1463","Pseudomonas putida KT2440, iJN746","Saccharomyces cerevisiae S288C,iMM904","Saccharomyces cerevisiae S288C,iND750","Salmonella enterica subsp. enterica serovar Typhimurium str. LT2","Salmonella pan-reactome","Shigella boydii CDC 3083-94","Shigella boydii Sb227","Shigella dysenteriae Sd197","Shigella flexneri 2002017","Shigella flexneri 2a str. 2457T","Shigella flexneri 2a str. 301","Shigella flexneri 5 str. 8401","Shigella sonnei Ss046","Staphylococcus aureus subsp. aureus N315","Staphylococcus aureus subsp. aureus USA300_TCH1516","Synechococcus elongatus PCC 7942","Synechocystis sp. PCC 6803","Synechocystis sp. PCC 6803, iSynCJ816","Thermotoga maritima MSB8","Trypanosoma cruzi Dm28c, iIS312","Trypanosoma cruzi Dm28c, iIS312_Amastigote","Trypanosoma cruzi Dm28c, iIS312_Epimastigote","Trypanosoma cruzi Dm28c, iIS312_Trypomastigote","Yersinia pestis CO92"]),
        "format": StrParam(
            default_value="json", human_name="File format", short_description="Output file format",
            allowed_values=["json", "xml", "xml.gz"])}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        id_organism: str = params["organism"]
        if params["organism"]:
            if params["name_organism"]:
                raise Exception ("You have entered an organism ID and selected an organism name, please choose between the two.")
            else :
                id_organism: str = params["organism"]
        elif params["name_organism"]:
            name_organism: str = params["name_organism"]
            #If the name is selected, we search for the corresponding ID in the file
            file_id_name = pd.read_csv(os.path.join(os.path.abspath(os.path.dirname(__file__)), "Bigg_numeroID_name.csv"), header=0, index_col=0,delimiter = ";")
            i = 0
            for organism in file_id_name["Organism"].values:
                if organism == name_organism :
                    id_organism = file_id_name.index[i]
                i += 1
        else :
            raise Exception ("You must either enter an organism ID or select the name of an organism.")

        output_format: str = params["format"]
        file_name = f"{id_organism}.{output_format}"
        url = f"http://bigg.ucsd.edu/static/models/{file_name}"
        #Retrieve the model from BiGG website
        command = f'curl -0 "{url}" > {file_name}'
        os.system(command)
        return {"output": File(file_name)}
