import os
import re
import shlex
import urllib.request
from typing import Dict, List, Set

import pandas as pd

from gws_core import (
    ConfigParams,
    ConfigSpecs,
    File,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    ResourceSet,
    ShellProxy,
    StrParam,
    Table,
    TableImporter,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingStyle,
    task_decorator,
)

from .kegg_r_env_task import KeggREnvHelper


_THIS_DIR = os.path.abspath(os.path.dirname(__file__))

# organism autocomplete list
KORG_PATH = os.path.join(_THIS_DIR, "list_organisms_pathview.txt")
_KORG = pd.read_csv(KORG_PATH, sep=None, engine="python", dtype=str, keep_default_na=False)

if "scientific.name" not in _KORG.columns or "kegg.code" not in _KORG.columns:
    raise Exception("list_organisms_pathview.txt must contain columns: scientific.name, kegg.code")

_KORG["scientific.name"] = _KORG["scientific.name"].astype(str).str.strip()
_KORG["kegg.code"] = _KORG["kegg.code"].astype(str).str.strip()

SUPPORTED_ORGANISM_NAMES = sorted([x for x in _KORG["scientific.name"].unique().tolist() if x and x.lower() != "nan"])
NAME_TO_KEGG = dict(zip(_KORG["scientific.name"], _KORG["kegg.code"]))
LOWER_NAME_TO_KEGG = {k.lower(): v for k, v in NAME_TO_KEGG.items() if k and k.lower() != "nan"}


def bh_adjust(pvals: List[float]) -> List[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    out = [1.0] * m
    prev = 1.0
    for rank in range(m):
        i = order[m - 1 - rank]
        q = pvals[i] * m / (m - rank)
        prev = min(prev, q)
        out[i] = min(1.0, prev)
    return out


def hypergeom_right_tail(N: int, K: int, n: int, k: int) -> float:
    import math
    if k <= 0:
        return 1.0
    max_x = min(K, n)

    def logC(a: int, b: int) -> float:
        return math.lgamma(a + 1) - math.lgamma(b + 1) - math.lgamma(a - b + 1)

    denom = logC(N, n)
    p = 0.0
    for x in range(k, max_x + 1):
        num = logC(K, x) + logC(N - K, n - x) - denom
        p += math.exp(num)
    return min(1.0, p)


@task_decorator(
    "KEGGVisualisation",
    human_name="KEGG enrichment analysis",
    short_description="Organism autocomplete -> Entrez->KEGG genes -> enrichment -> Pathview PNGs",
    style=TypingStyle.material_icon(material_icon_name="collections_bookmark", background_color="#d9d9d9"),
)
class KEGGVisualisation(Task):
    """
    KEGG enrichment + Pathview (Entrez -> KEGG gene IDs)

    This task expects a DEG table with an Entrez Gene ID column (NCBI GeneID).
    If you start from other identifiers (Ensembl, symbols, FlyBase IDs), first run
    the Omix “Gene ID conversion” task and set target namespace = ENTREZGENE.

    Workflow:
    1) Convert Entrez Gene IDs to KEGG gene IDs via KEGG REST (conv).
    2) Compute KEGG pathway enrichment (hypergeometric test + BH/FDR).
    3) Render up to N Pathview PNGs for the top enriched pathways.

    Notes:
    - overlap = number of your mapped genes present in a given pathway.
    - min_genes_mapped_required stops the pipeline if too few genes map to KEGG.
    - max_pathways_to_render limits the number of Pathview images produced.
    - Some KEGG “overview/global” maps may show little/no coloring due to node types.
    """


    input_specs = InputSpecs({
        "deg_file": InputSpec([File, Table], human_name="DEG table (CSV/TSV)"),
    })

    output_specs = OutputSpecs({
        "pathways": OutputSpec(ResourceSet, human_name="Pathview PNGs"),
        "kegg_enrichment": OutputSpec(Table, human_name="KEGG enrichment (with pathway names)"),
        "gene_kegg_used": OutputSpec(Table, human_name="Genes used (mapped) + pathway names"),
    })

    config_specs = ConfigSpecs({
        "organism_name": StrParam(allowed_values=SUPPORTED_ORGANISM_NAMES, human_name="Organism (autocomplete)"),

        "id_column": StrParam(default_value="gene_id", human_name="ID column (optional)"),
        "foldchange_column": StrParam(default_value="log2FoldChange", human_name="Fold-change column (optional)"),

        "col_entrez": StrParam(
            default_value="entrez",
            human_name="Entrez Gene list",
            short_description="Column with Entrez Gene IDs (e.g. 318213). Use 'Gene ID conversion' task to generate it",
        ),

        "min_genes_mapped_required": StrParam(default_value="10", human_name="Minimum mapped genes required"),
        "max_pathways_to_render": StrParam(default_value="30", human_name="Max pathways rendered by Pathview"),
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        shell: ShellProxy = KeggREnvHelper.create_proxy(self.message_dispatcher)

        organism_name = str(params["organism_name"]).strip()
        specie = self._specie_from_name(organism_name)
        self.log_info_message(f"Selected organism: {organism_name} -> KEGG code: {specie}")

        id_col = str(params.get("id_column", "index")).strip()
        fc_col = str(params.get("foldchange_column", "log2FoldChange")).strip()
        col_entrez = (params.get("col_entrez") or "").strip()

        min_mapped = int(str(params.get("min_genes_mapped_required", "10")).strip() or "10")
        top_n = int(str(params.get("max_pathways_to_render", "30")).strip() or "30")

        #  Pathview only if overlap > 1
        MIN_OVERLAP_TO_RENDER = 1

        deg_path = self._materialize_input(inputs["deg_file"], shell)

        # validate input columns early
        header_df = pd.read_csv(deg_path, sep=None, engine="python", dtype=str, keep_default_na=False, nrows=1)
        cols = set(header_df.columns.tolist())
        if col_entrez == "":
            raise Exception("col_entrez is empty. Please set the Entrez column name.")
        if col_entrez not in cols:
            raise Exception(f"col_entrez='{col_entrez}' not found in input columns: {sorted(cols)}")

        # 1) resolve genes (Entrez only)
        resolver_py = os.path.join(_THIS_DIR, "_kegg_resolve_gene_ids.py")
        out_used = os.path.join(shell.working_dir, "gene_kegg_used.csv")
        out_gene_kegg = os.path.join(shell.working_dir, "gene_kegg.csv")
        out_dbg = os.path.join(shell.working_dir, "mapping_debug.csv")  # internal

        cmd = " ".join([
            "python3", shlex.quote(resolver_py),
            "--deg", shlex.quote(deg_path),
            "--specie", shlex.quote(specie),
            "--id_col", shlex.quote(id_col),
            "--fc_col", shlex.quote(fc_col),
            "--col_entrez", shlex.quote(col_entrez),
            "--min_mapped", shlex.quote(str(min_mapped)),
            "--out_used", shlex.quote(out_used),
            "--out_gene_kegg", shlex.quote(out_gene_kegg),
            "--out_debug", shlex.quote(out_dbg),
        ])

        rc = shell.run(cmd, shell_mode=True)
        if rc != 0 or (not os.path.exists(out_gene_kegg)) or os.path.getsize(out_gene_kegg) == 0:
            raise Exception("KEGG resolver failed. Check internal mapping_debug.csv/gene_kegg_used.csv in run folder.")

        used_df = pd.read_csv(out_used, dtype=str, keep_default_na=False)
        used_df["kegg_full"] = used_df.get("kegg_full", "").astype(str).str.strip()
        mapped = used_df[used_df["kegg_full"] != ""].copy()

        self.log_info_message(f"Mapped rows to KEGG genes: {mapped.shape[0]}/{used_df.shape[0]}")
        if mapped.shape[0] < min_mapped:
            raise Exception(f"Too few genes mapped to KEGG ({mapped.shape[0]} < {min_mapped}).")

        # 2) universe
        gp = self._kegg_link_pathway_species(specie)
        if gp.empty:
            raise Exception("KEGG link/pathway/<specie> returned empty universe (network/proxy or parsing issue).")

        universe = set(gp["gene"].tolist())
        pw2genes: Dict[str, Set[str]] = {}
        gene2pws: Dict[str, Set[str]] = {}
        for _, r in gp.iterrows():
            pw2genes.setdefault(r["pathway"], set()).add(r["gene"])
            gene2pws.setdefault(r["gene"], set()).add(r["pathway"])

        query = sorted(set(mapped["kegg_full"].astype(str).tolist()))
        query = [g for g in query if g in universe]
        N = len(universe)
        n = len(query)
        if n == 0:
            raise Exception("Query genes do not intersect KEGG universe. Check kegg_full formatting/universe parsing.")

        # 3) pathway names
        pw_names_df = self._kegg_list_pathways(specie)
        pw_name_map = dict(zip(pw_names_df["pathway"], pw_names_df["pathway_name"]))

        # add pathway ids + names into gene_kegg_used
        def join_sorted(xs: Set[str]) -> str:
            return ";".join(sorted(xs)) if xs else ""

        def join_names(pws: Set[str]) -> str:
            if not pws:
                return ""
            names = [pw_name_map.get(p, "") for p in sorted(pws)]
            names = [x for x in names if x]
            return ";".join(names)

        used_df["pathways"] = used_df["kegg_full"].map(lambda g: join_sorted(gene2pws.get(g, set())))
        used_df["pathway_names"] = used_df["kegg_full"].map(lambda g: join_names(gene2pws.get(g, set())))
        used_df.to_csv(out_used, index=False)

        # 4) enrichment
        rows = []
        qset = set(query)
        for pw, geneset in pw2genes.items():
            K = len(geneset)
            k = len(qset & geneset)  # overlap
            if k == 0:
                continue
            p = hypergeom_right_tail(N, K, n, k)
            rows.append((pw, k, K, n, N, p))

        if not rows:
            raise Exception("Enrichment table is empty (no overlaps).")

        enr = pd.DataFrame(rows, columns=[
            "pathway", "overlap", "pathway_size", "query_size", "universe_size", "pvalue"
        ])
        enr["padj"] = bh_adjust(enr["pvalue"].tolist())
        enr = enr.sort_values(["padj", "pvalue", "overlap"], ascending=[True, True, False]).reset_index(drop=True)
        enr["pathway_name"] = enr["pathway"].map(lambda p: pw_name_map.get(p, ""))

        enr_csv = os.path.join(shell.working_dir, "kegg_enrichment.csv")
        enr.to_csv(enr_csv, index=False)

        # 5) pathview (✅ filter overlap > 2)
        def to_pid5(pw: str) -> str:
            digs = "".join(ch for ch in str(pw) if ch.isdigit())
            return digs[-5:] if len(digs) >= 5 else ""

        enr_render = enr[enr["overlap"] >= MIN_OVERLAP_TO_RENDER].copy()

        # Fallback: if nothing passes, don't produce 0 images silently
        if enr_render.empty:
            self.log_info_message(
                f"No pathways with overlap >= {MIN_OVERLAP_TO_RENDER}. Falling back to top {max(1, top_n)} pathways."
            )
            enr_render = enr.copy()

        pids = [to_pid5(x) for x in enr_render.head(max(1, top_n))["pathway"].astype(str).tolist()]
        pids = [x for x in pids if x]

        pathway_list = os.path.join(shell.working_dir, "pathway_kegg.txt")
        with open(pathway_list, "w") as f:
            f.write("\n".join(pids))

        kegg_dir = os.path.join(shell.working_dir, "kegg_cache")
        os.makedirs(kegg_dir, exist_ok=True)
        self._prefetch_kegg_files(specie, pids, kegg_dir)

        fold_change = "Yes" if ("log2FoldChange" in pd.read_csv(out_gene_kegg, nrows=1).columns) else "No"
        r_script = os.path.join(_THIS_DIR, "kegg_visualisation.R")
        cmd_r = " ".join([
            "Rscript", "--vanilla", shlex.quote(r_script),
            shlex.quote(out_gene_kegg),
            shlex.quote(specie),
            shlex.quote(pathway_list),
            shlex.quote(fold_change),
            shlex.quote(kegg_dir),
        ])
        rc = shell.run(cmd_r, shell_mode=True)
        if rc != 0:
            raise Exception("R/pathview crashed. Check internal pathway_debug.csv in run folder.")

        # collect pngs
        rs = ResourceSet()
        rs.name = "Pathview images"
        for fn in os.listdir(shell.working_dir):
            fp = os.path.join(shell.working_dir, fn)
            if os.path.isfile(fp) and (fn.endswith(".pathview.png") or fn.endswith(".pathview.multi.png")):
                rs.add_resource(File(fp), fn)

        gene_kegg_used_tbl = TableImporter.call(File(out_used), params={"index_column": -1})
        kegg_enrichment_tbl = TableImporter.call(File(enr_csv), params={"index_column": -1})

        return {
            "pathways": rs,
            "kegg_enrichment": kegg_enrichment_tbl,
            "gene_kegg_used": gene_kegg_used_tbl,
        }

    def _specie_from_name(self, organism_name: str) -> str:
        if organism_name in NAME_TO_KEGG:
            return NAME_TO_KEGG[organism_name]
        low = organism_name.lower()
        if low in LOWER_NAME_TO_KEGG:
            return LOWER_NAME_TO_KEGG[low]
        raise Exception(f"Organism '{organism_name}' not found in list_organisms_pathview.txt")

    def _materialize_input(self, inp, shell: ShellProxy) -> str:
        if isinstance(inp, Table):
            p = os.path.join(shell.working_dir, "deg_input.csv")
            inp.to_dataframe().to_csv(p, index=False)
            return p
        return inp.path

    def _fetch(self, url: str, timeout: int = 180) -> str:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")

    def _kegg_link_pathway_species(self, specie: str) -> pd.DataFrame:
        url = f"https://rest.kegg.jp/link/pathway/{specie}"
        raw = self._fetch(url, timeout=240)

        head = raw.lstrip()[:300].lower()
        if head.startswith("<!doctype") or head.startswith("<html") or "forbidden" in head or "error" in head:
            sample = "\n".join(raw.splitlines()[:10])
            raise Exception(f"Unexpected KEGG response for {url}. First lines:\n{sample}")

        genes, pws = [], []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue

            if "\t" in line:
                left, right = line.split("\t", 1)
            else:
                parts = line.split(None, 1)
                if len(parts) < 2:
                    continue
                left, right = parts[0], parts[1]

            left, right = left.strip(), right.strip()

            if left.startswith(specie + ":") and right.startswith("path:"):
                gene = left
                pw = right.replace("path:", "")
            elif right.startswith(specie + ":") and left.startswith("path:"):
                gene = right
                pw = left.replace("path:", "")
            else:
                continue

            if re.fullmatch(rf"{re.escape(specie)}\d{{5}}", pw):
                genes.append(gene)
                pws.append(pw)

        return pd.DataFrame({"gene": genes, "pathway": pws})

    def _kegg_list_pathways(self, specie: str) -> pd.DataFrame:
        url = f"https://rest.kegg.jp/list/pathway/{specie}"
        raw = self._fetch(url, timeout=240)

        ids, names = [], []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            a, b = line.split("\t", 1)
            pid = a.replace("path:", "").strip()
            name = b.strip()
            if re.fullmatch(rf"{re.escape(specie)}\d{{5}}", pid):
                ids.append(pid)
                names.append(name)

        return pd.DataFrame({"pathway": ids, "pathway_name": names})

    def _download(self, url: str, out_path: str) -> None:
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                data = resp.read()
            with open(out_path, "wb") as f:
                f.write(data)
        except Exception:
            pass

    def _prefetch_kegg_files(self, specie: str, pathways_5: List[str], kegg_dir: str) -> None:
        for pid in pathways_5:
            base = f"{specie}{pid}"
            xml_path = os.path.join(kegg_dir, f"{base}.xml")
            png_path = os.path.join(kegg_dir, f"{base}.png")
            if not os.path.exists(xml_path):
                self._download(f"https://rest.kegg.jp/get/{base}/kgml", xml_path)
            if not os.path.exists(png_path):
                self._download(f"https://rest.kegg.jp/get/{base}/image", png_path)
