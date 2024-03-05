# Load required libraries
library(readr)
library(pathview)
library(foreach)
library(doParallel)

# Read command-line arguments
args <- commandArgs(trailingOnly = TRUE)

if (length(args)==0) { # test if there is at least one argument: if not, return an error
  stop("At least one argument must be supplied (input file).", call.=FALSE)
} else {
  # retrieve the different arguments
  list_gene_entrez_path = args[1]
  specie = args[2]
  pathway_kegg_path = args[3]
  fold_change = args[4]
}

#load data
list_gene_entrez <- read.csv(list_gene_entrez_path, header = TRUE, sep = ",", row.names = 1)
pathway_kegg <- read.table(pathway_kegg_path, quote="\"", comment.char="")

#Map genes on KEGG pathway for each pathway

list_pathway_error <- list() #list to keep the pathways that gives an error with the function pathview. 

# Register parallel backend
cores <- detectCores()
cl <- makeCluster(cores)
registerDoParallel(cl)

if (fold_change == "Yes"){ #If the fold change values are provided, we give the column of the genes and the valeus to pathview 
  run_pathview <- function(pathway, gene_data, specie) {
      try_pathview <- try(suppressMessages(pathview(gene.data = list_gene_entrez, pathway.id = pathway, gene.idtype = "entrez", species = specie)), silent = TRUE)
      return(list(try_pathview = try_pathview, pathway = pathway))
    }
  # Perform parallel execution of pathview for each pathway
  pathway_results <- foreach(pathway = pathway_kegg$V1, .packages = c("pathview")) %dopar% {
  run_pathview(pathway, list_gene_entrez, specie)}

  for (result in pathway_results) {
    if (class(result$try_pathview) == "try-error"){
      print(paste0("An error has occurred -> the pathway ", result$pathway, " cannot be displayed." ))
      #append name pathview to end of list
      len <- length(list_pathway_error)
      list_pathway_error[[len+1]] <- result$pathway
    }
  }
} else{  #If the fold change values are not provided, we only give the column of the genes to pathview 
  run_pathview <- function(pathway, gene_data, specie) {
      try_pathview <- try(suppressMessages(pathview(gene.data = row.names(list_gene_entrez), pathway.id = pathway, gene.idtype = "entrez", species = specie)), silent = TRUE)
      return(list(try_pathview = try_pathview, pathway = pathway))
    }
  # Perform parallel execution of pathview for each pathway
  pathway_results <- foreach(pathway = pathway_kegg$V1, .packages = c("pathview")) %dopar% {
  run_pathview(pathway, list_gene_entrez, specie)}

  for (result in pathway_results) {
    if (class(result$try_pathview) == "try-error"){
      print(paste0("An error has occurred -> the pathway ", result$pathway, " cannot be displayed." ))
      #append name pathview to end of list
      len <- length(list_pathway_error)
      list_pathway_error[[len+1]] <- result$pathway
    }
  }
}

# Close parallel backend
stopCluster(cl)

write.csv(list_pathway_error, file = "list_pathway_error.csv", row.names = FALSE)