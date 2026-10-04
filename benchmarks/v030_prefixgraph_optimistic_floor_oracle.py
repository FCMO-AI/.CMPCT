from __future__ import annotations

"""Optimistic structural floor for the Shifted PrefixGraph family.

Domination preregistration
--------------------------
Strict target: every frozen row must be strictly smaller *and* strictly faster to create than ZIP/Deflate and
solid Zstd-19 while preserving accepted-v0.29 and all product invariants.
Diagnosis: D4 representation/physical-layout red on Shifted size, with separate runtime/RSS debt already measured.
Instrument radicality: R0, used to decide whether the next admissible primary move must be R4.
Saturation: S2/S4 pressure is active after repeated PrefixGraph runtime/RSS rehabilitation misses; this oracle is
intended to prevent another search/parameter iteration if the representation itself has no possible byte headroom.
RPS: 92/100 (necessity 15, upside 20, causal fit 15, generality 7, information 15, efficiency 10,
composability 7, simplicity 3).

Referee / pre-mortem
--------------------
The strongest criticism of another PrefixGraph experiment is that we may be optimizing an already-losing
representation.  This oracle therefore gives the family impossible advantages rather than trying to predict a
shipping selector: every member may independently use the best raw-prefix payload from *any* nominated anchor,
including anchors that would themselves have to remain direct in a realizable depth-1 forest; the normal minimum
payload-saving threshold is removed; and metadata is charged as zero bytes.  Only unavoidable header, payload,
and footer bytes remain.  If even that impossible-best-case archive is not strictly smaller than solid Zstd-19,
no selector, branch-and-bound rule, worker count, metadata shaving, or two/multi-anchor search inside this raw
prefix family can close the size gap.  That is an S1 floor and the family must be retired as the primary Shifted
size route.  If the floor is below Zstd-19, the representation still has theoretical headroom, but this result
alone does not prove a realizable or fast product path.

Builder / decisive instrument
-----------------------------
Use the exact frozen Shifted generator, canonical r25 filesystem staging, the shipping PrefixGraph raw/dictionary
compressors, and the exact external solid-Zstd harness.  The bound is deliberately *more optimistic* than any
valid PrefixGraph archive and therefore safe only as a lower bound, never as a release-size claim.

Hostile-review contract
-----------------------
A positive headroom result earns no release credit and must not be described as a candidate win.  A negative
headroom result is decisive only for this raw-prefix/depth-1 payload family under the measured compressor; it does
not prove that a different representation cannot beat Zstd.  Benchmark identity is confined to this research
oracle and is never consulted by production selection policy.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_prefixgraph as PG

TARGET = ("resemblance_hostile_v1", "01_shifted_versions")


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
    anchors = PG._anchor_indices(len(raws))
    if not anchors:
        raise RuntimeError("Shifted stage exposed no PrefixGraph anchors")

    # Start at the exact direct payload floor.  Then grant each member the smallest prefix payload emitted by any
    # nominated anchor, even when that anchor could not legally remain an anchor in the same realizable forest.
    # We also deliberately ignore MIN_PREFIX_PAYLOAD_SAVING.  Both choices can only make the bound smaller.
    best_payload_sizes = [len(payload) for payload in direct]
    best_sources = ["direct" for _ in raws]
    exact_prefix_trials = 0
    for anchor in anchors:
        compressor, _dictionary = PG._prefix_codec(raws[anchor])
        for index, raw in enumerate(raws):
            if index == anchor or not raw or not raws[anchor]:
                continue
            payload = compressor.compress(raw)
            exact_prefix_trials += 1
            if len(payload) < best_payload_sizes[index]:
                best_payload_sizes[index] = len(payload)
                best_sources[index] = f"anchor:{anchor}"

    payload_floor = sum(best_payload_sizes)
    fixed_framing_floor = PG.HEADER.size + payload_floor + PG.FOOTER.size
    improved_members = sum(source != "direct" for source in best_sources)

    shipping = work_root / "shipping-prefixgraph.cmpct"
    PG.build(staged, shipping)
    verified = PG.strong_verify(shipping)
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError("shipping PrefixGraph baseline failed exact tree verification")
    shipping_bytes = shipping.stat().st_size
    if fixed_framing_floor > shipping_bytes:
        raise RuntimeError("optimistic PrefixGraph floor exceeded a realizable shipping archive")

    ext_parent = work_root / "external"
    ext_parent.mkdir()
    normalized = EXT._normalized_stage(source, ext_parent)
    external_tree = EXT._tree(normalized)
    zip_row = EXT._zip(normalized, work_root / "shifted.zip", work_root / "zip-extracted")
    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir()
    zstd_row = EXT._tar_zstd(
        normalized,
        work_root / "shifted.tar.zst",
        work_root / "zstd-extracted",
        zstd_work,
    )
    EXT._verify_extracted(work_root / "zip-extracted", external_tree, "ZIP")
    if not zstd_row.get("available"):
        raise RuntimeError("solid Zstd-19 comparator unavailable; structural floor cannot be classified")
    EXT._verify_extracted(work_root / "zstd-extracted", external_tree, "Zstd-19")

    zip_bytes = int(zip_row["archive_bytes"])
    zstd_bytes = int(zstd_row["archive_bytes"])
    headroom_vs_zstd = zstd_bytes - fixed_framing_floor
    shipping_gap_vs_zstd = shipping_bytes - zstd_bytes
    floor_can_beat_zstd = fixed_framing_floor < zstd_bytes
    decision = "ESCALATE_RADICALITY" if not floor_can_beat_zstd else "ITERATE_SAME_FAMILY"

    return {
        "schema": "cmpct-v030-prefixgraph-optimistic-structural-floor-v1",
        "target": f"{TARGET[0]}/{TARGET[1]}",
        "diagnosis": "D4",
        "instrument_radicality": "R0",
        "minimum_primary_radicality_if_floor_fails": "R4",
        "active_saturation": ["S2", "S4"],
        "research_priority_score": 92,
        "r25_manifest_encoding": "filesystem-v1",
        "files": len(raws),
        "nominated_anchors": len(anchors),
        "exact_prefix_trials": exact_prefix_trials,
        "optimistically_prefix_improved_members": improved_members,
        "optimistic_payload_floor_bytes": payload_floor,
        "optimistic_fixed_framing_floor_bytes": fixed_framing_floor,
        "optimistic_metadata_bytes_charged": 0,
        "optimistic_allows_unrealizable_anchor_reuse": True,
        "optimistic_ignores_minimum_prefix_saving": True,
        "shipping_prefixgraph_bytes": shipping_bytes,
        "shipping_prefixgraph_sha256": hashlib.sha256(shipping.read_bytes()).hexdigest(),
        "maximum_theoretical_saving_vs_shipping_bytes": shipping_bytes - fixed_framing_floor,
        "zip_bytes": zip_bytes,
        "zstd19_bytes": zstd_bytes,
        "shipping_gap_vs_zstd19_bytes": shipping_gap_vs_zstd,
        "optimistic_headroom_vs_zstd19_bytes": headroom_vs_zstd,
        "optimistic_floor_strictly_beats_zstd19": floor_can_beat_zstd,
        "tree_sha256": expected_tree,
        "verified_tree_sha256": verified.get("tree_sha256"),
        "external_tree_sha256": external_tree,
        "oracle_elapsed_s": time.perf_counter() - started,
        "release_credit": False,
        "decision": decision,
        "next_decisive_test": (
            "retire raw-prefix depth-1 size family and invent a new R4 Shifted representation"
            if not floor_can_beat_zstd
            else "measure the smallest realizable bounded multi-anchor forest needed to consume the proven headroom"
        ),
        "claim_boundary": (
            "Impossible-best-case lower bound only. A passing headroom result is not a candidate archive claim; "
            "a failing bound proves the current raw-prefix payload family cannot beat Zstd-19 even with free metadata."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-floor-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-floor.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
