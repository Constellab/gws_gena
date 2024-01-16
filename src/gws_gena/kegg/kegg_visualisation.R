# Load required libraries
library(readr)
library(pathview)

# Read command-line arguments
args <- commandArgs(trailingOnly = TRUE)

if (length(args)==0) { # test if there is at least one argument: if not, return an error
  stop("At least one argument must be supplied (input file).", call.=FALSE)
} else {
  # retrieve the different arguments
  list_gene_entrez_path = args[1]
  specie = args[2]
  pathway_kegg_path = args[3]
  pathway_kegg_ok_path = args[4]
  fold_change = args[5]
}

#load data
list_gene_entrez <- read.csv(list_gene_entrez_path, header = TRUE, sep = ",", row.names = 1)
pathway_kegg <- read.table(pathway_kegg_path, quote="\"", comment.char="")
#pathway_kegg_ok is a list made by hand, where pathview should work and give a clean result 
pathway_kegg_ok <-read.table(pathway_kegg_ok_path, colClasses = c("character"), quote="\"", comment.char="")



#Add the specie in the names of pathways ok, in order to match with "pathway_kegg"
pathway_kegg_ok$V1 <- paste(specie, pathway_kegg_ok$V1, sep = "")

#Map genes on KEGG pathway for each pathway

if (fold_change == "Yes"){ #If the fold change values are provided, we give the column of the genes and the valeus to pathview 
  for(pathway in pathway_kegg$V1){
    if (pathway %in% pathway_kegg_ok$V1){
      pv.out = pathview(gene.data = list_gene_entrez, pathway.id = pathway, gene.idtype = "entrez", species = specie)
    }
  }
} else{  #If the fold change values are not provided, we only give the column of the genes to pathview 
  for(pathway in pathway_kegg$V1){
    if (pathway %in% pathway_kegg_ok$V1){
      pv.out = pathview(gene.data = row.names(list_gene_entrez), pathway.id = pathway, gene.idtype = "entrez", species = specie)
    }
  }
}