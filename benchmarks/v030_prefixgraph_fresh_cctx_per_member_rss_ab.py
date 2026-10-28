from __future__ import annotations

"""Exact canonical PrefixGraph persistent-vs-fresh CCtx RSS A/B.

Diagnostic only. It changes no production module and grants no release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_profile_isolation as ISO

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
ROUNDS = 3
PG = ISO.PG
EXPECTED_MODULE = "experiments._v030_canonical_prefixgraph"
EXPECTED_MAGIC = b"CMP25PG\0"


def rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def assert_exact_owner() -> None:
    if PG.__name__ != EXPECTED_MODULE or PG.MAGIC != EXPECTED_MAGIC or ISO.RC.PG is not PG:
        raise RuntimeError("wrong canonical PrefixGraph semantic owner")
    ISO.assert_research_modules_unchanged()


class FreshPerMemberCompressor:
    """Same dictionary/level semantics, but one CCtx lifetime per sibling trial."""

    def __init__(self, dictionary) -> None:
        self.dictionary = dictionary

    def compress(self, raw: bytes) -> bytes:
        compressor = PG.zstd.ZstdCompressor(level=PG.PAYLOAD_LEVEL, dict_data=self.dictionary)
        return compressor.compress(raw)


def fresh_prefix_codec(prefix: bytes):
    dictionary = PG.zstd.ZstdCompressionDict(prefix, dict_type=PG.zstd.DICT_TYPE_RAWCONTENT)
    return FreshPerMemberCompressor(dictionary), dictionary


def with_codec(mode: str):
    if mode == "baseline":
        return PG._prefix_codec
    if mode == "fresh":
        return fresh_prefix_codec
    raise ValueError(mode)


def build_worker(mode: str, source: Path, archive: Path) -> dict:
    assert_exact_owner()
    expected_tree = PG.treehash(source)
    original = PG._prefix_codec
    PG._prefix_codec = with_codec(mode)
    baseline = rss_kib()
    started = time.perf_counter()
    try:
        stats = PG.build(source, archive)
    finally:
        PG._prefix_codec = original
    wall_s = time.perf_counter() - started
    peak = rss_kib()
    verify = PG.strong_verify(archive)
    if verify.get("ok") is not True or verify.get("tree_sha256") != expected_tree:
        raise RuntimeError("strong verification mismatch")
    payload = archive.read_bytes()
    return {
        "mode": mode,
        "owner_module": PG.__name__,
        "archive_bytes": len(payload),
        "archive_sha256": hashlib.sha256(payload).hexdigest(),
        "tree_sha256": expected_tree,
        "selected_anchor": stats.get("anchor"),
        "anchor_auditions": stats.get("anchor_auditions"),
        "baseline_rss_kib": baseline,
        "peak_rss_kib": peak,
        "incremental_peak_rss_kib": peak - baseline,
        "wall_s": wall_s,
        "verification": verify,
    }


def identity_worker(mode: str, source: Path) -> dict:
    assert_exact_owner()
    files = sorted(p for p in source.rglob("*") if p.is_file())
    rels = [p.relative_to(source).as_posix() for p in files]
    raws = [p.read_bytes() for p in files]
    if not raws or len(raws) > PG.MAX_FILES or any(len(raw) > PG.MAX_FILE_BYTES for raw in raws):
        raise RuntimeError("invalid PrefixGraph identity corpus")
    tree = PG._treehash_parts(rels, raws)
    direct_payloads = [PG._compress(raw) for raw in raws]
    original = PG._prefix_codec
    PG._prefix_codec = with_codec(mode)
    rows = []
    try:
        for anchor in [None, *PG._anchor_indices(len(raws))]:
            blob, stats = PG._serialize_candidate(rels, raws, direct_payloads, tree, anchor)
            rows.append({
                "anchor": anchor,
                "archive_bytes": len(blob),
                "archive_sha256": hashlib.sha256(blob).hexdigest(),
                "prefix_records": stats.get("prefix_records"),
                "payload_saving_bytes": stats.get("payload_saving_bytes"),
            })
    finally:
        PG._prefix_codec = original
    return {"mode": mode, "owner_module": PG.__name__, "tree_sha256": tree, "candidates": rows}


def run_worker(mode: str, source: Path, archive: Path | None = None) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cmd = [sys.executable, __file__, "--worker-mode", mode, "--worker-source", str(source)]
    if archive is not None:
        cmd += ["--worker-archive", str(archive)]
    done = subprocess.run(cmd, cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    lines = [line for line in done.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"worker emitted no JSON: {mode}")
    return json.loads(lines[-1])


def median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(row[key]) for row in rows))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]

    baseline_identity = run_worker("identity-baseline", source)
    candidate_identity = run_worker("identity-fresh", source)
    baseline_pairs = [
        (r["anchor"], r["archive_bytes"], r["archive_sha256"], r["prefix_records"], r["payload_saving_bytes"])
        for r in baseline_identity["candidates"]
    ]
    candidate_pairs = [
        (r["anchor"], r["archive_bytes"], r["archive_sha256"], r["prefix_records"], r["payload_saving_bytes"])
        for r in candidate_identity["candidates"]
    ]
    full_candidate_identity = (
        baseline_identity["tree_sha256"] == candidate_identity["tree_sha256"]
        and baseline_identity["owner_module"] == candidate_identity["owner_module"] == EXPECTED_MODULE
        and baseline_pairs == candidate_pairs
    )

    rows: dict[str, list[dict]] = {"baseline": [], "fresh": []}
    for round_index in range(ROUNDS):
        order = ["baseline", "fresh"] if round_index % 2 == 0 else ["fresh", "baseline"]
        for mode in order:
            archive = work_root / "archives" / f"round-{round_index}-{mode}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            rows[mode].append(run_worker(f"build-{mode}", source, archive))

    build_ids = {
        (r["archive_bytes"], r["archive_sha256"], r["tree_sha256"], r["selected_anchor"], r["anchor_auditions"])
        for mode_rows in rows.values() for r in mode_rows
    }
    build_identity = len(build_ids) == 1
    baseline_inc = median(rows["baseline"], "incremental_peak_rss_kib")
    fresh_inc = median(rows["fresh"], "incremental_peak_rss_kib")
    baseline_peak = median(rows["baseline"], "peak_rss_kib")
    fresh_peak = median(rows["fresh"], "peak_rss_kib")
    baseline_wall = median(rows["baseline"], "wall_s")
    fresh_wall = median(rows["fresh"], "wall_s")
    rss_reduction = 1.0 - fresh_inc / baseline_inc if baseline_inc > 0 else 0.0
    wall_ratio = fresh_wall / baseline_wall if baseline_wall > 0 else float("inf")
    experiment_valid = bool(full_candidate_identity and build_identity)
    if not experiment_valid:
        decision = "INVALID_EXACT_BYTE_IDENTITY"
    elif rss_reduction >= 0.20 and wall_ratio <= 1.25:
        decision = "FRESH_CCTX_LIFETIME_REHAB_SUPPORTED"
    elif rss_reduction < 0.10:
        decision = "FRESH_CCTX_LIFETIME_RETIRED_AS_PRIMARY_OWNER"
    else:
        decision = "FRESH_CCTX_LIFETIME_AMBIGUOUS"

    return {
        "schema": "cmpct-v030-prefixgraph-fresh-cctx-per-member-rss-ab-v1",
        "source_commit": source_commit(),
        "target": list(TARGET),
        "rounds": ROUNDS,
        "identity": {
            "baseline": baseline_identity,
            "fresh": candidate_identity,
            "full_candidate_set_byte_identical": full_candidate_identity,
            "build_identity": build_identity,
        },
        "rows": rows,
        "summary": {
            "baseline_median_incremental_peak_rss_kib": baseline_inc,
            "fresh_median_incremental_peak_rss_kib": fresh_inc,
            "baseline_median_peak_rss_kib": baseline_peak,
            "fresh_median_peak_rss_kib": fresh_peak,
            "baseline_median_wall_s": baseline_wall,
            "fresh_median_wall_s": fresh_wall,
            "rss_reduction": rss_reduction,
            "wall_ratio": wall_ratio,
            "decision": decision,
        },
        "gate": {"experiment_valid": experiment_valid},
        "contract": {
            "support_threshold": 0.20,
            "retire_threshold": 0.10,
            "max_supported_wall_ratio": 1.25,
            "compressor_level_changed": False,
            "dictionary_bytes_changed": False,
            "candidate_set_changed": False,
            "production_change": False,
            "release_credit": False,
        },
        "release_credit": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker-mode")
    parser.add_argument("--worker-source", type=Path)
    parser.add_argument("--worker-archive", type=Path)
    args = parser.parse_args()
    if args.worker_mode:
        if args.worker_source is None:
            raise SystemExit("--worker-source required")
        if args.worker_mode == "identity-baseline":
            result = identity_worker("baseline", args.worker_source)
        elif args.worker_mode == "identity-fresh":
            result = identity_worker("fresh", args.worker_source)
        elif args.worker_mode == "build-baseline":
            result = build_worker("baseline", args.worker_source, args.worker_archive)
        elif args.worker_mode == "build-fresh":
            result = build_worker("fresh", args.worker_source, args.worker_archive)
        else:
            raise SystemExit(f"unknown worker mode {args.worker_mode}")
        print(json.dumps(result, sort_keys=True))
        return
    if args.work_root is None or args.output is None:
        raise SystemExit("--work-root and --output required")
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": result["summary"], "gate": result["gate"]}, indent=2))


if __name__ == "__main__":
    main()
