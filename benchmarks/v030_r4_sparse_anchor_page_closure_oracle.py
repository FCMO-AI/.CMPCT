from __future__ import annotations

"""Page-closure oracle for the v0.30 R4 cold sparse-anchor reader.

Mission Lock / Referee
======================
The byte-level token-anchor oracle showed <=1.011x decoded dependency closure for fixed 4 KiB reads.
The cold reader, however, services a dependency crossing a page boundary by calling ``read()`` on the
source range; ``read()`` materializes the *entire* source page through ``_decode_page`` before slicing.
That changes the dependency unit from a byte/token to a 4 KiB page and may recursively widen a very
small byte dependency cone into many complete pages.

Falsifiable hypothesis: the observed hosted cold-reader failure/very high work is explained by this
page-granularity expansion.  Build the exact byte parent graph already allowed to the diagnostic
oracle, derive the induced page DAG without executing the cold reader, and compute the transitive page
closure for the same fixed 4 KiB request set.

Disproof: if every request's transitive page closure is <=8 pages (32 KiB decoded work) and the graph
has shallow bounded depth, page expansion does not explain the failure and the next investigation must
return to token parsing/correctness.  If any request exceeds 8 pages, preserve that as a mechanism-level
negative for the current full-page recursive reader; do not "fix" it by raising the 8x locality limit.

This is diagnostic-only.  The builder may inspect the full byte parent graph; no such graph is credited
to a shipping reader and no product-format semantics change.
"""

import argparse
import hashlib
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
from benchmarks import v030_r4_deflate_physical_range_oracle as PHYS
from benchmarks import v030_r4_deflate_token_anchor_physical_oracle as TOKEN

SCHEMA = "cmpct-v030-r4-sparse-anchor-page-closure-oracle-v1"
PAGE = 4096
DECODE_LIMIT = 8 * PAGE


def _page_graph(parents: list[int], n: int) -> list[set[int]]:
    pages = math.ceil(n / PAGE)
    edges: list[set[int]] = [set() for _ in range(pages)]
    for child, parent in enumerate(parents):
        if parent < 0:
            continue
        cp = child // PAGE
        pp = parent // PAGE
        if pp != cp:
            if pp > cp:
                raise RuntimeError("non-causal DEFLATE parent edge")
            edges[cp].add(pp)
    return edges


def _closure(edges: list[set[int]], roots: set[int]) -> tuple[set[int], int]:
    seen: set[int] = set()
    memo_depth: dict[int, int] = {}

    def depth(p: int, active: set[int]) -> int:
        if p in memo_depth:
            return memo_depth[p]
        if p in active:
            raise RuntimeError("cycle in page dependency graph")
        active.add(p)
        d = 1
        for q in edges[p]:
            d = max(d, 1 + depth(q, active))
        active.remove(p)
        memo_depth[p] = d
        return d

    stack = list(roots)
    while stack:
        p = stack.pop()
        if p in seen:
            continue
        seen.add(p)
        stack.extend(edges[p] - seen)
    max_depth = max((depth(p, set()) for p in roots), default=0)
    return seen, max_depth


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(
        V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "r4_sparse_page_closure_neutral",
    )
    repair = V029._load(V029.REPAIR_PATH, "r4_sparse_page_closure_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "04_analytics_and_database"
    rel = DUAL._npz_relation(source)["accepted"]
    npz = source.joinpath(*Path(rel["npz_path"]).parts)
    info, comp, expected, method = CONE._raw_zip_member(npz, rel["member"])
    if method != zipfile.ZIP_DEFLATED:
        raise RuntimeError("expected DEFLATE")

    t0 = time.perf_counter()
    parsed = PHYS.parse_physical(comp)
    parse_wall = time.perf_counter() - t0
    actual = zlib.decompress(comp, -15)
    if actual != expected or len(parsed["parents"]) != len(actual):
        raise RuntimeError("physical parser mismatch")

    edges = _page_graph(parsed["parents"], len(actual))
    edge_count = sum(len(x) for x in edges)
    cross_parent_bytes = sum(
        1
        for child, parent in enumerate(parsed["parents"])
        if parent >= 0 and child // PAGE != parent // PAGE
    )

    requests = TOKEN.starts(len(actual))
    rows = []
    worst = None
    total_pages = 0
    over_limit = 0
    for start in requests:
        end = min(start + PAGE, len(actual))
        roots = set(range(start // PAGE, (end - 1) // PAGE + 1))
        closure, depth = _closure(edges, roots)
        decoded = sum(min(PAGE, len(actual) - p * PAGE) for p in closure)
        row = {
            "start": start,
            "end": end,
            "request_bytes": end - start,
            "root_pages": len(roots),
            "transitive_pages": len(closure),
            "transitive_page_ids": sorted(closure),
            "decoded_page_bytes": decoded,
            "decoded_page_amplification": decoded / max(1, end - start),
            "dependency_depth_pages": depth,
        }
        rows.append(row)
        total_pages += len(closure)
        if decoded > DECODE_LIMIT:
            over_limit += 1
        if worst is None or (decoded, depth) > (worst["decoded_page_bytes"], worst["dependency_depth_pages"]):
            worst = row

    assert worst is not None
    supported = over_limit == 0
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "04_analytics_and_database",
        "member": {
            "compressed_bytes": len(comp),
            "compressed_sha256": hashlib.sha256(comp).hexdigest(),
            "raw_bytes": len(actual),
            "raw_sha256": hashlib.sha256(actual).hexdigest(),
            "crc32": info.CRC,
        },
        "parser": {
            "parse_wall_s": parse_wall,
            "pages": len(edges),
            "page_dependency_edges": edge_count,
            "bytes_whose_parent_crosses_page": cross_parent_bytes,
        },
        "page_closure": {
            "page_bytes": PAGE,
            "decoded_work_limit_bytes": DECODE_LIMIT,
            "requests": len(requests),
            "requests_over_8x_decoded_page_work": over_limit,
            "mean_transitive_pages": total_pages / len(requests),
            "worst": worst,
            "passes_page_granularity_8x_floor": supported,
        },
        "hypothesis": {
            "full_page_recursive_materialization_explains_resource_debt": not supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "full_parent_graph_is_oracle_only": True,
            "same_fixed_request_set": True,
            "no_page_size_sweep": True,
            "no_threshold_sweep": True,
            "no_product_format_change": True,
        },
        "interpretation": (
            "Current whole-page recursive cold-reader mechanism is falsified by decoded-work expansion; "
            "the next reader must retain sub-page/token dependency granularity or another bounded seed mechanism."
            if not supported
            else
            "Page closure remains within 8x; investigate the executing reader's token parser/correctness and measured CPU next."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-page-closure-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-page-closure.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"member": d["member"], "parser": d["parser"], "page_closure": d["page_closure"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
