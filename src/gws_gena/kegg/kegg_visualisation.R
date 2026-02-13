#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly=TRUE)
gene_csv    <- args[[1]]
specie      <- args[[2]]
pathway_txt <- args[[3]]
fold_change <- args[[4]]   # "Yes" / "No"
kegg_dir    <- args[[5]]

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(pathview)
})

df <- read_csv(gene_csv, show_col_types = FALSE)

if (!("kegg_short" %in% colnames(df))) {
  colnames(df)[1] <- "kegg_short"
}

df <- df %>% filter(!is.na(kegg_short), kegg_short != "")

if (nrow(df) == 0) {
  write.csv(data.frame(pathway=character(), level="ERROR", message="gene_kegg.csv empty"),
            "pathway_debug.csv", row.names=FALSE)
  quit(status=1)
}

if (fold_change == "Yes" && ("log2FoldChange" %in% colnames(df))) {
  vals <- suppressWarnings(as.numeric(df$log2FoldChange))
  names(vals) <- df$kegg_short
  gene.data <- vals
} else {
  vals <- rep(1, nrow(df))
  names(vals) <- df$kegg_short
  gene.data <- vals
}

pids <- readLines(pathway_txt, warn=FALSE)
pids <- trimws(pids)
pids <- pids[pids != ""]

if (length(pids) == 0) {
  write.csv(data.frame(pathway=character(), level="ERROR", message="No pathways provided"),
            "pathway_debug.csv", row.names=FALSE)
  quit(status=1)
}

dbg <- data.frame(pathway=character(), level=character(), message=character(),
                  stringsAsFactors=FALSE)

for (pid in pids) {
  tryCatch({
    pathview(
      gene.data = gene.data,
      pathway.id = pid,
      species = specie,
      gene.idtype = "kegg",
      kegg.native = TRUE,
      same.layer = FALSE,
      kegg.dir = kegg_dir,
      out.suffix = "pathview"
    )
    dbg <- rbind(dbg, data.frame(pathway=pid, level="INFO", message="OK",
                                 stringsAsFactors=FALSE))
  }, error=function(e) {
    dbg <- rbind(dbg, data.frame(pathway=pid, level="ERROR",
                                 message=as.character(e$message),
                                 stringsAsFactors=FALSE))
  })
}

write.csv(dbg, "pathway_debug.csv", row.names=FALSE)
