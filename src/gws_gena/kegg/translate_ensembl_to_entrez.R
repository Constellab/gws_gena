# Load required libraries
library(readr)
library(gprofiler2)
library(dplyr)

# Read command-line arguments
args <- commandArgs(trailingOnly = TRUE)

if (length(args)==0) { # test if there is at least one argument: if not, return an error
  stop("At least one argument must be supplied (input file).", call.=FALSE)
} else {
  # retrieve the different arguments
  list_gene_ensembl_path = args[1]
  organism = args[2]
}

#load data
full_table <- read.csv(list_gene_ensembl_path, header = 0, row.names=1, sep =",")

result_convert = gconvert(query = row.names(full_table), organism = organism,
                          target="entrezgene_acc", mthreshold = 1, filter_na = FALSE)

if (all(is.na(result_convert$target))){ #If it doesn't work with entrezgene_acc; then try with entrezgene
  result_convert = gconvert(query = row.names(full_table), organism = organism,
                          target="entrezgene", mthreshold = 1, filter_na = FALSE)
}
full_table$convert_entrez = result_convert$target

full_table <- na.omit(full_table)

# Reorder the columns with 'convert_entrez' as the first column
full_table <- full_table %>% select(convert_entrez, everything())

# Write the csv file into the result folder
result_path <- "gene_entrez.csv"
write.csv(full_table, file = result_path, row.names = FALSE, col.names = TRUE)
