from __future__ import annotations

"""Page-level ownership oracle for rehabilitating Analytics Mode2 locality.

The exact sparse decoded-byte oracle found a worst 4 KiB closure of only ~1.01x, but an index per
DEFLATE token is economically impossible. This oracle asks whether the sparse relation survives a much
coarser representation boundary that a real reader could plausibly index: fixed 4 KiB decoded pages.

For each decoded page, any LZ77 parent outside that page creates a dependency edge to the source page.
We then compute the exact transitive page closure. A reader that can independently enter each page at a
recorded compressed-token anchor would decode every page in that closure. This deliberately gifts the
compressed-bit anchor machinery, Huffman-state metadata, physical range fragmentation and authentication;
therefore it is a lower-bound architecture test, not release credit.

Pre-registered disproof: if any 4 KiB page has a transitive closure >8 pages, reject 4 KiB page ownership
as sufficient for the <=8x decoded-work contract. If all closures are <=8 pages, the next experiment must
build/charge physical token anchors, block state and authenticated pread ranges. No page-size sweep.
"""

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import time
import zipfile
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_sparse_dependency_oracle as SPARSE

SCHEMA = "cmpct-v030-r4-deflate-page-dependency-oracle-v1"
PAGE = 4096
LIMIT_PAGES = 8
DUAL_OWNER_BYTES = 4_453_188
ACCEPTED_V029_ANALYTICS = DUAL.ACCEPTED_V029_ANALYTICS
ANCHOR_BYTES = 16
BLOCK_STATE_BYTES = 64  # deliberately generous envelope, not a claimed final encoding


def page_graph(parents, n: int) -> list[set[int]]:
    pages = math.ceil(n / PAGE)
    edges = [set() for _ in range(pages)]
    for out, parent in enumerate(parents):
        if parent < 0:
            continue
        p_out = out // PAGE
        p_src = parent // PAGE
        if p_src != p_out:
            edges[p_out].add(p_src)
    return edges


def closure(edges: list[set[int]], root: int) -> set[int]:
    seen = {root}
    stack = [root]
    while stack:
        p = stack.pop()
        for q in edges[p]:
            if q not in seen:
                seen.add(q)
                stack.append(q)
    return seen


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_r4_page_dep_neutral")
    repair = V029._load(V029.REPAIR_PATH, "cmpct_r4_page_dep_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "04_analytics_and_database"

    relation = DUAL._npz_relation(source)["accepted"]
    npz = source.joinpath(*Path(relation["npz_path"]).parts)
    info, comp, expected, method = CONE._raw_zip_member(npz, relation["member"])
    if method != zipfile.ZIP_DEFLATED:
        raise RuntimeError(f"expected DEFLATE member, got method={method}")

    t0 = time.perf_counter()
    parsed = SPARSE.parse_parents(comp)
    parse_wall = time.perf_counter() - t0
    actual = zlib.decompress(comp, -15)
    if actual != expected or len(parsed["parents"]) != len(actual):
        raise RuntimeError("dependency parser mismatch")

    edges = page_graph(parsed["parents"], len(actual))
    worst = None
    total_pages = 0
    closure_t0 = time.perf_counter()
    cross_edges = sum(len(x) for x in edges)
    for page in range(len(edges)):
        c = closure(edges, page)
        total_pages += len(c)
        row = {
            "page": page,
            "out_start": page * PAGE,
            "out_end": min((page + 1) * PAGE, len(actual)),
            "closure_pages": len(c),
            "decoded_bytes_upper_bound": sum(min(PAGE, len(actual) - p * PAGE) for p in c),
            "dependency_pages": sorted(c - {page}),
        }
        row["amplification_vs_4KiB_request"] = row["decoded_bytes_upper_bound"] / PAGE
        if worst is None or row["closure_pages"] > worst["closure_pages"]:
            worst = row
    closure_wall = time.perf_counter() - closure_t0
    assert worst is not None

    aux_budget = ACCEPTED_V029_ANALYTICS - DUAL_OWNER_BYTES
    anchor_bytes = len(edges) * ANCHOR_BYTES
    block_state_bytes = parsed["blocks"] * BLOCK_STATE_BYTES
    simple_index = anchor_bytes + block_state_bytes
    passes = worst["closure_pages"] <= LIMIT_PAGES
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "04_analytics_and_database",
        "relation": relation,
        "member": {
            "compressed_bytes": len(comp),
            "raw_bytes": len(actual),
            "crc32": info.CRC,
            "compress_type": info.compress_type,
        },
        "parser": {
            "blocks": parsed["blocks"],
            "tokens": parsed["tokens"],
            "literal_tokens": parsed["literal_tokens"],
            "copy_tokens": parsed["copy_tokens"],
            "exact_raw_match": True,
            "parse_wall_s": parse_wall,
        },
        "page_dependency": {
            "page_bytes": PAGE,
            "pages": len(edges),
            "cross_page_edges": cross_edges,
            "mean_closure_pages": total_pages / len(edges),
            "worst": worst,
            "limit_pages_per_4KiB_request": LIMIT_PAGES,
            "passes_page_floor": passes,
            "closure_wall_s": closure_wall,
        },
        "economics": {
            "dual_owner_bytes": DUAL_OWNER_BYTES,
            "accepted_v029_bytes": ACCEPTED_V029_ANALYTICS,
            "max_auxiliary_bytes_to_beat_v029": aux_budget,
            "illustrative_anchor_bytes": anchor_bytes,
            "illustrative_block_state_bytes": block_state_bytes,
            "illustrative_simple_index_bytes": simple_index,
            "illustrative_simple_index_within_budget": simple_index <= aux_budget,
        },
        "hypothesis": {
            "4KiB_page_ownership_can_meet_8x_decoded_lower_bound": passes,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "no_product_format_change": True,
            "no_page_size_sweep": True,
            "lower_bound_only": True,
            "important_limitation": "gifts actual token-anchor encoding, Huffman-state encoding, compressed physical I/O, authentication and range fragmentation; pass authorizes a physical prototype but is not a locality claim",
        },
        "next_if_supported": "build a physical 4KiB page-anchor reader prototype, authenticate compressed ranges, and measure actual pread bytes plus decoded pages under the 1.682 MB auxiliary budget",
        "next_if_falsified": "preserve negative and change owner boundary; do not tune page size against this workload",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-deflate-page-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-deflate-page.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(json.dumps({"member":d["member"],"parser":d["parser"],"page_dependency":d["page_dependency"],"economics":d["economics"],"hypothesis":d["hypothesis"]},indent=2))


if __name__ == "__main__":
    main()
