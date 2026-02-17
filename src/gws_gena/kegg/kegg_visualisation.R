#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly=TRUE)
gene_csv      <- args[[1]]
specie        <- args[[2]]
pathway_txt   <- args[[3]]
fc_cols_arg   <- args[[4]]   # "log2FC_A,log2FC_B,..."
kegg_dir      <- args[[5]]

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
  write.csv(data.frame(pathway=character(), message=character()),
            "list_pathway_error.csv", row.names=FALSE)
  quit(status=1)
}

# Parse fold-change columns
fc_cols <- unlist(strsplit(fc_cols_arg, ",", fixed=TRUE))
fc_cols <- trimws(fc_cols)
fc_cols <- fc_cols[fc_cols != ""]

missing <- fc_cols[!(fc_cols %in% colnames(df))]
if (length(missing) > 0) {
  write.csv(data.frame(pathway=character(), level="ERROR",
                       message=paste0("Missing FC columns: ", paste(missing, collapse=", "))),
            "pathway_debug.csv", row.names=FALSE)
  write.csv(data.frame(pathway=character(), message=character()),
            "list_pathway_error.csv", row.names=FALSE)
  quit(status=1)
}

# Read pathways list
pids <- readLines(pathway_txt, warn=FALSE)
pids <- trimws(pids)
pids <- pids[pids != ""]
if (length(pids) == 0) {
  write.csv(data.frame(pathway=character(), level="ERROR", message="No pathways provided"),
            "pathway_debug.csv", row.names=FALSE)
  write.csv(data.frame(pathway=character(), message=character()),
            "list_pathway_error.csv", row.names=FALSE)
  quit(status=1)
}

# Build gene data:
# - if >=2 FC columns => multi-state matrix (box is split into sub-boxes)
# - if 1 FC column => normal vector
# Always use full IDs "dme:xxxxx"
gene_ids <- paste0(specie, ":", df$kegg_short)

dbg <- data.frame(pathway=character(), level=character(), message=character(),
                  stringsAsFactors=FALSE)

for (pid in pids) {
  tryCatch({
    if (length(fc_cols) >= 2) {
      mat <- as.matrix(sapply(fc_cols, function(cn) suppressWarnings(as.numeric(df[[cn]]))))
      colnames(mat) <- fc_cols
      rownames(mat) <- gene_ids

      # Force a comparable color scale across conditions (same palette range)
      # You said you want -1..+1 for the same scale:
      mat[mat >  1] <-  1
      mat[mat < -1] <- -1

      pathview(
        gene.data   = mat,
        pathway.id  = pid,
        species     = specie,
        gene.idtype = "kegg",
        kegg.native = TRUE,
        same.layer  = FALSE,
        multi.state = TRUE,
        kegg.dir    = kegg_dir,
        out.suffix  = "pathview_multistate",
        limit       = list(gene = 1, cpd = 1)
      )
    } else if (length(fc_cols) == 1) {
      v <- suppressWarnings(as.numeric(df[[fc_cols[1]]]))
      names(v) <- gene_ids
      v[v >  1] <-  1
      v[v < -1] <- -1

      pathview(
        gene.data   = v,
        pathway.id  = pid,
        species     = specie,
        gene.idtype = "kegg",
        kegg.native = TRUE,
        same.layer  = FALSE,
        kegg.dir    = kegg_dir,
        out.suffix  = paste0("pathview_", fc_cols[1]),
        limit       = list(gene = 1, cpd = 1)
      )
    } else {
      # no FC columns => constant
      v <- rep(1, length(gene_ids))
      names(v) <- gene_ids
      pathview(
        gene.data   = v,
        pathway.id  = pid,
        species     = specie,
        gene.idtype = "kegg",
        kegg.native = TRUE,
        same.layer  = FALSE,
        kegg.dir    = kegg_dir,
        out.suffix  = "pathview_const"
      )
    }

    dbg <- rbind(dbg, data.frame(pathway=pid, level="INFO", message="OK", stringsAsFactors=FALSE))
  }, error=function(e) {
    dbg <- rbind(dbg, data.frame(pathway=pid, level="ERROR", message=as.character(e$message),
                                 stringsAsFactors=FALSE))
  })
}

write.csv(dbg, "pathway_debug.csv", row.names=FALSE)
write.csv(subset(dbg, level=="ERROR")[, c("pathway","message")], "list_pathway_error.csv", row.names=FALSE)
