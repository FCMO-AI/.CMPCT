from __future__ import annotations

"""R4 structural falsifier: exact three-anchor depth-1 PrefixGraph capacity on Shifted.

The prior exhaustive two-anchor oracle is a measured miss, while the impossible-best prefix floor remains far
below solid Zstd-19. This is therefore the smallest justified representation-capacity escalation. We reuse the
same exact anchor->member payload trials, enumerate every three-anchor set, price the complete archive with the
real metadata/framing law, materialize only the winning triple, and verify it through the unchanged PrefixGraph
reader. Exhaustive search time is diagnostic and earns no product creation-time or release credit.
"""

import argparse
from itertools import combinations
import hashlib
import json
from pathlib import Path
import shutil
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_performance as PERF
from benchmarks import v030_prefixgraph_two_anchor_representation_oracle as BASE
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_prefixgraph as PG

TARGET = BASE.TARGET
ANCHOR_COUNT = 3


def run(work_root: Path) -> dict:
    started = time.perf_counter()
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]

    staged = work_root / "r25-stage"
    CANON._prepare_profile_tree(source, staged)
    files = sorted(path for path in staged.rglob("*") if path.is_file())
    rels = [path.relative_to(staged).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]
    if not raws or len(raws) > PG.MAX_FILES or any(len(raw) > PG.MAX_FILE_BYTES for raw in raws):
        raise RuntimeError("Shifted r25 stage left PrefixGraph representation envelope")
    expected_tree = PG._treehash_parts(rels, raws)
    direct = [PG._compress(raw) for raw in raws]
    nominated = PG._anchor_indices(len(raws))
    if len(nominated) < ANCHOR_COUNT:
        raise RuntimeError("Shifted stage does not expose three nominated PrefixGraph anchors")

    # Each expensive prefix payload is constructed exactly once. Triple enumeration below performs only exact
    # integer/metadata pricing and therefore cannot hide a different compression result behind an approximation.
    trials: dict[int, list[tuple[int, bytes] | None]] = {}
    exact_prefix_trials = 0
    for anchor in nominated:
        compressor, _dictionary = PG._prefix_codec(raws[anchor])
        row: list[tuple[int, bytes] | None] = []
        for index, raw in enumerate(raws):
            if index == anchor or not raw or not raws[anchor]:
                row.append(None)
                continue
            payload = compressor.compress(raw)
            row.append((len(payload), PG.H(payload)))
            exact_prefix_trials += 1
        trials[anchor] = row

    shipping = work_root / "shipping-prefixgraph.cmpct"
    PG.build(staged, shipping)
    all_direct_price = BASE._price(rels, raws, direct, expected_tree, (), trials)[0]
    single_prices = {anchor: BASE._price(rels, raws, direct, expected_tree, (anchor,), trials)[0] for anchor in nominated}
    projected_shipping = min([all_direct_price, *single_prices.values()])
    if projected_shipping != shipping.stat().st_size:
        raise RuntimeError(
            f"triple oracle single-anchor pricing drift: projected={projected_shipping} shipping={shipping.stat().st_size}"
        )

    best = None
    evaluated = 0
    for triple in combinations(nominated, ANCHOR_COUNT):
        priced, records, _meta = BASE._price(rels, raws, direct, expected_tree, tuple(triple), trials)
        evaluated += 1
        key = (priced, tuple(triple))
        if best is None or key < best[0]:
            best = (key, tuple(triple), records)
    if best is None:
        raise RuntimeError("three-anchor representation enumeration produced no candidate")

    best_bytes = int(best[0][0])
    best_triple = best[1]
    records = best[2]
    candidate = work_root / "three-anchor-prefixgraph.cmpct"
    BASE._materialize(candidate, rels, raws, direct, expected_tree, best_triple, records)
    if candidate.stat().st_size != best_bytes:
        raise RuntimeError("materialized three-anchor archive differs from exact projected price")
    verified = PG.strong_verify(candidate)
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError("existing PrefixGraph reader rejected three-anchor depth-1 forest")

    ext_parent = work_root / "external"
    ext_parent.mkdir()
    normalized = EXT._normalized_stage(source, ext_parent)
    zip_row = EXT._zip(normalized, work_root / "shifted.zip", work_root / "zip-extracted")
    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir()
    zstd_row = EXT._tar_zstd(normalized, work_root / "shifted.tar.zst", work_root / "zstd-extracted", zstd_work)
    source_tree = EXT._tree(normalized)
    EXT._verify_extracted(work_root / "zip-extracted", source_tree, "ZIP")
    if zstd_row.get("available"):
        EXT._verify_extracted(work_root / "zstd-extracted", source_tree, "Zstd-19")

    zstd_bytes = int(zstd_row["archive_bytes"]) if zstd_row.get("available") else None
    strict_size_win = bool(
        best_bytes < int(zip_row["archive_bytes"]) and zstd_bytes is not None and best_bytes < zstd_bytes
    )
    saving_vs_shipping = shipping.stat().st_size - best_bytes
    margin_vs_zstd = None if zstd_bytes is None else zstd_bytes - best_bytes
    decision = "PROMOTE_NEXT_PREREQUISITE" if strict_size_win else "RETIRE_FAMILY"
    next_test = (
        "derive a bounded content-agnostic three-anchor selector and account complete creation time"
        if strict_size_win
        else "replace small-global-anchor expansion with a different representation class (member clustering/segment-owned bases or non-prefix transform)"
    )
    return {
        "schema": "cmpct-v030-prefixgraph-three-anchor-representation-oracle-v1",
        "target": f"{TARGET[0]}/{TARGET[1]}",
        "r25_manifest_encoding": "filesystem-v1",
        "files": len(raws),
        "nominated_anchors": len(nominated),
        "anchor_count": ANCHOR_COUNT,
        "evaluated_triples": evaluated,
        "exact_prefix_trials": exact_prefix_trials,
        "single_anchor_pricing_exact": True,
        "shipping_prefixgraph_bytes": shipping.stat().st_size,
        "shipping_prefixgraph_sha256": hashlib.sha256(shipping.read_bytes()).hexdigest(),
        "three_anchor_bytes": best_bytes,
        "three_anchor_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
        "best_triple": list(best_triple),
        "saving_vs_shipping_prefixgraph_bytes": saving_vs_shipping,
        "zip_bytes": int(zip_row["archive_bytes"]),
        "zstd19_bytes": zstd_bytes,
        "margin_vs_zstd19_bytes": margin_vs_zstd,
        "strict_size_win_vs_zip_and_zstd19": strict_size_win,
        "reader_reused_without_depth_change": True,
        "max_dependency_depth": 1,
        "tree_sha256": expected_tree,
        "verified_tree_sha256": verified.get("tree_sha256"),
        "oracle_elapsed_s": time.perf_counter() - started,
        "release_credit": False,
        "product_create_time_claim": False,
        "domination_audit": {
            "strict_target": "15/15 strictly smaller and faster than ZIP/Deflate and solid Zstd-19",
            "diagnosis": "D4",
            "radicality": "R4",
            "active_saturation": ["S2", "S4"],
            "research_priority_score": 96,
            "measured_gap_change_bytes": saving_vs_shipping,
            "strongest_self_critique": (
                "Three global anchors may still be the wrong abstraction: the optimistic floor permits each member its best base, "
                "so a miss here would show that small global anchor sets cannot capture the proven theoretical headroom."
            ),
            "terminal_decision": decision,
            "next_decisive_test": next_test,
        },
        "decision": decision,
        "claim_boundary": (
            "R4 structural capacity oracle only. Exhaustive triple enumeration is not a product selector, does not claim "
            "creation-time competitiveness, and grants zero release credit."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-three-anchor-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-three-anchor.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
