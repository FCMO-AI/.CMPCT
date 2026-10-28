from __future__ import annotations

"""Exact-byte PrefixGraph anchor-audition scheduling oracle.

PrefixGraph anchor candidates are independent complete-artifact auditions over immutable
source/direct-payload bytes.  The shipping research builder currently serializes up to
32 such auditions.  This oracle changes only their schedule: direct Zstd payloads remain
computed exactly once, then admissible anchors are serialized through a bounded thread
pool and the identical complete-byte tournament selects the winner.

The experiment targets the two frozen workloads where PrefixGraph is known to be the
complete r25 winner while the enclosing product still spends substantial wall time.
It is research-only: no selector/terminal rule changes here.  A scheduling result earns
promotion consideration only when serial and parallel archives are byte/SHA/tree
identical on every round and parallel build time improves by >=20% and >=1 second on
each target.  Integrity, recovery, locality and archive grammar are unchanged.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_prefixgraph_terminal_parity_oracle as TERM
from experiments import entropygraph_v030_prefixgraph as PG
from experiments import entropygraph_v030_release_candidate as RC

TARGETS = frozenset({"shifted_versions", "boundary_churn"})
ROUNDS = 3
MAX_WORKERS = 4
MIN_RELATIVE_IMPROVEMENT = 0.20
MIN_ABSOLUTE_SAVING_S = 1.0


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parallel_build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files or len(files) > PG.MAX_FILES:
        raise ValueError("PrefixGraph requires 1..MAX_FILES regular files")
    rels = [path.relative_to(root).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]
    if any(len(raw) > PG.MAX_FILE_BYTES for raw in raws):
        raise ValueError("PrefixGraph research seed file ceiling exceeded")
    expected_tree = PG._treehash_parts(rels, raws)

    direct_payloads = [PG._compress(raw) for raw in raws]
    all_direct, direct_stats = PG._serialize_candidate(rels, raws, direct_payloads, expected_tree, None)
    anchors = PG._anchor_indices(len(raws))
    workers = max(1, min(MAX_WORKERS, os.cpu_count() or 1, len(anchors) or 1))

    def audition(anchor: int):
        return PG._serialize_candidate(rels, raws, direct_payloads, expected_tree, anchor)

    audition_started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="cmpct-prefixgraph") as pool:
        anchor_candidates = list(pool.map(audition, anchors))
    audition_s = time.perf_counter() - audition_started

    candidates = [(all_direct, direct_stats), *anchor_candidates]
    blob, stats = min(
        candidates,
        key=lambda item: (len(item[0]), -1 if item[1]["anchor"] is None else item[1]["anchor"]),
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    stats = dict(stats)
    stats.update({
        "archive_bytes": len(blob),
        "all_direct_bytes": len(all_direct),
        "saving_vs_all_direct_bytes": len(all_direct) - len(blob),
        "anchor_auditions": len(anchors),
        "files": len(files),
        "logical_bytes": sum(map(len, raws)),
        "tree_sha256": expected_tree,
        "create_s": time.perf_counter() - started,
        "anchor_audition_s": audition_s,
        "workers": workers,
        "max_dependency_depth": 1 if stats["prefix_records"] else 0,
    })
    return stats


def _find_targets(work_root: Path) -> list[tuple[str, Path]]:
    _accepted, roots = TERM._corpora(work_root)
    found: dict[str, tuple[str, Path]] = {}
    for suite, root in roots:
        for source in sorted(path for path in root.iterdir() if path.is_dir()):
            if source.name in TARGETS:
                found[source.name] = (suite, source)
    missing = sorted(TARGETS - found.keys())
    if missing:
        raise RuntimeError(f"missing frozen PrefixGraph target workloads: {missing}")
    return [found[name] for name in sorted(TARGETS)]


def _measure_one(suite: str, source: Path, root: Path) -> dict:
    expected_tree = RC.treehash(source)
    eligible, reject = RC._prefixgraph_eligibility(source, expected_tree)
    if not eligible:
        raise RuntimeError(f"{suite}/{source.name} unexpectedly PrefixGraph-ineligible: {reject}")

    serial_samples: list[float] = []
    parallel_samples: list[float] = []
    audition_samples: list[float] = []
    reference_sha: str | None = None
    reference_bytes: int | None = None
    selected_anchor: int | None = None
    workers: int | None = None

    for round_index in range(ROUNDS):
        round_root = root / f"round-{round_index}"
        round_root.mkdir(parents=True, exist_ok=True)
        serial_path = round_root / "serial.cmpct"
        parallel_path = round_root / "parallel.cmpct"

        # Alternate order to avoid fixed warm-cache/order advantage.
        if round_index % 2 == 0:
            started = time.perf_counter(); serial_stats = dict(PG.build(source, serial_path)); serial_elapsed = time.perf_counter() - started
            started = time.perf_counter(); parallel_stats = dict(_parallel_build(source, parallel_path)); parallel_elapsed = time.perf_counter() - started
        else:
            started = time.perf_counter(); parallel_stats = dict(_parallel_build(source, parallel_path)); parallel_elapsed = time.perf_counter() - started
            started = time.perf_counter(); serial_stats = dict(PG.build(source, serial_path)); serial_elapsed = time.perf_counter() - started

        serial_blob = serial_path.read_bytes(); parallel_blob = parallel_path.read_bytes()
        if serial_blob != parallel_blob:
            raise RuntimeError(f"parallel PrefixGraph changed archive bytes for {suite}/{source.name}")
        serial_verify = PG.strong_verify(serial_path); parallel_verify = PG.strong_verify(parallel_path)
        if serial_verify.get("tree_sha256") != expected_tree or parallel_verify.get("tree_sha256") != expected_tree:
            raise RuntimeError(f"PrefixGraph tree identity drift for {suite}/{source.name}")
        locality = RC._prefixgraph_locality(parallel_path)
        if not locality.get("passed"):
            raise RuntimeError(f"parallel PrefixGraph exceeded release locality for {suite}/{source.name}")
        if serial_stats["anchor"] != parallel_stats["anchor"]:
            raise RuntimeError(f"parallel PrefixGraph changed winning anchor for {suite}/{source.name}")

        digest = _sha_bytes(serial_blob)
        if reference_sha is None:
            reference_sha = digest; reference_bytes = len(serial_blob); selected_anchor = serial_stats["anchor"]
        elif digest != reference_sha or len(serial_blob) != reference_bytes:
            raise RuntimeError(f"PrefixGraph serial reference nondeterminism for {suite}/{source.name}")

        serial_samples.append(float(serial_elapsed)); parallel_samples.append(float(parallel_elapsed))
        audition_samples.append(float(parallel_stats["anchor_audition_s"])); workers = int(parallel_stats["workers"])

    serial_median = statistics.median(serial_samples)
    parallel_median = statistics.median(parallel_samples)
    saving = serial_median - parallel_median
    relative = saving / max(serial_median, 1e-12)
    material = relative >= MIN_RELATIVE_IMPROVEMENT and saving >= MIN_ABSOLUTE_SAVING_S
    return {
        "label": f"{suite}/{source.name}",
        "archive_bytes": int(reference_bytes),
        "archive_sha256": reference_sha,
        "selected_anchor": selected_anchor,
        "rounds": ROUNDS,
        "workers": workers,
        "serial_create_s": serial_samples,
        "parallel_create_s": parallel_samples,
        "median_serial_create_s": float(serial_median),
        "median_parallel_create_s": float(parallel_median),
        "median_parallel_anchor_audition_s": float(statistics.median(audition_samples)),
        "absolute_saving_s": float(saving),
        "relative_improvement": float(relative),
        "exact_archive_identity": True,
        "exact_tree_identity": True,
        "within_release_locality": True,
        "material_speedup": bool(material),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    targets = _find_targets(work_root / "corpus")
    rows = []
    for suite, source in targets:
        with tempfile.TemporaryDirectory(prefix="cmpct-pg-parallel-", dir=work_root) as td:
            row = _measure_one(suite, source, Path(td))
        rows.append(row)
        print(json.dumps(row, separators=(",", ":")), flush=True)
    gate = {
        "exact_target_count": len(rows) == len(TARGETS),
        "exact_archive_identity_all": all(row["exact_archive_identity"] for row in rows),
        "exact_tree_identity_all": all(row["exact_tree_identity"] for row in rows),
        "locality_green_all": all(row["within_release_locality"] for row in rows),
        "material_speedup_all": all(row["material_speedup"] for row in rows),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-prefixgraph-parallel-anchor-v1",
        "targets": sorted(TARGETS),
        "scheduling_change": {
            "type": "bounded-thread-parallel-independent-anchor-auditions",
            "max_workers": MAX_WORKERS,
            "candidate_set_unchanged": True,
            "complete_byte_tournament_unchanged": True,
            "direct_payload_floor_unchanged": True,
        },
        "rows": rows,
        "gate": gate,
        "claim_boundary": (
            "Research-only exact-byte scheduling proof. It cannot change PrefixGraph eligibility, candidate set, "
            "winner selection, outer r25 tournament or release authority. Promotion requires exact byte/tree/locality "
            "identity and the frozen material speed hurdle on every target, followed by ordinary all-15 validation."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-parallel-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-parallel.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": result["rows"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("PrefixGraph parallel anchor scheduling did not earn promotion")


if __name__ == "__main__":
    main()
