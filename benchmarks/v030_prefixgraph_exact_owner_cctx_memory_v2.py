from __future__ import annotations

"""Exact canonical PrefixGraph CCtx memory attribution v2.

Research-only diagnostic. The measured PrefixGraph owner is the private canonical clone
used by r25 shipping, not the historical parallel research wrapper.
"""

import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_profile_isolation as ISO

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
ROUNDS = 2
PG = ISO.PG
EXPECTED_MODULE = "experiments._v030_canonical_prefixgraph"
EXPECTED_MAGIC = b"CMP25PG\0"


def rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def assert_exact_owner() -> None:
    if PG.__name__ != EXPECTED_MODULE:
        raise RuntimeError(f"wrong PrefixGraph semantic owner: {PG.__name__}")
    if PG.MAGIC != EXPECTED_MAGIC:
        raise RuntimeError(f"wrong canonical PrefixGraph magic: {PG.MAGIC!r}")
    if ISO.RC.PG is not PG:
        raise RuntimeError("release-candidate PrefixGraph owner is not profile-isolation PG")
    ISO.assert_research_modules_unchanged()


def source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def profile_contexts(source: Path) -> dict:
    assert_exact_owner()
    files = sorted(path for path in source.rglob("*") if path.is_file())
    rels = [path.relative_to(source).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]
    if not raws or len(raws) > PG.MAX_FILES:
        raise RuntimeError("invalid exact-owner PrefixGraph corpus")
    if any(len(raw) > PG.MAX_FILE_BYTES for raw in raws):
        raise RuntimeError("exact-owner PrefixGraph file ceiling exceeded")
    tree = PG._treehash_parts(rels, raws)
    direct_payloads = [PG._compress(raw) for raw in raws]
    anchors = PG._anchor_indices(len(raws))
    baseline = rss_kib()
    rows = []
    for anchor in anchors:
        compressor, dictionary = PG._prefix_codec(raws[anchor])
        if not hasattr(compressor, "memory_size"):
            raise RuntimeError("ZstdCompressor.memory_size() unavailable")
        samples = [int(compressor.memory_size())]
        trials = 0
        for index, raw in enumerate(raws):
            if index == anchor or not raw or not raws[anchor]:
                continue
            trial = compressor.compress(raw)
            trials += 1
            samples.append(int(compressor.memory_size()))
            del trial
        rows.append({
            "anchor": int(anchor),
            "anchor_raw_bytes": len(raws[anchor]),
            "compressed_trials": trials,
            "initial_cctx_bytes": samples[0],
            "peak_reported_cctx_bytes": max(samples),
            "final_reported_cctx_bytes": samples[-1],
        })
        del compressor, dictionary
        gc.collect()
    peak = rss_kib()
    return {
        "owner_module": PG.__name__,
        "tree_sha256": tree,
        "files": len(files),
        "logical_bytes": sum(map(len, raws)),
        "direct_payload_bytes": sum(map(len, direct_payloads)),
        "anchors": rows,
        "baseline_rss_kib": baseline,
        "peak_rss_kib": peak,
        "incremental_peak_rss_kib": peak - baseline,
    }


def exact_build(source: Path, archive: Path) -> dict:
    assert_exact_owner()
    expected_tree = PG.treehash(source)
    baseline = rss_kib()
    started = __import__("time").perf_counter()
    stats = PG.build(source, archive)
    wall_s = __import__("time").perf_counter() - started
    peak = rss_kib()
    verify = PG.strong_verify(archive)
    if verify.get("ok") is not True or verify.get("tree_sha256") != expected_tree:
        raise RuntimeError("exact-owner PrefixGraph strong verification mismatch")
    payload = archive.read_bytes()
    return {
        "owner_module": PG.__name__,
        "archive_bytes": len(payload),
        "archive_sha256": hashlib.sha256(payload).hexdigest(),
        "tree_sha256": expected_tree,
        "wall_s": wall_s,
        "baseline_rss_kib": baseline,
        "peak_rss_kib": peak,
        "incremental_peak_rss_kib": peak - baseline,
        "anchor_auditions": stats.get("anchor_auditions"),
        "verification": verify,
    }


def run_worker(mode: str, source: Path, archive: Path | None = None) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cmd = [sys.executable, __file__, "--worker-mode", mode, "--worker-source", str(source)]
    if archive is not None:
        cmd.extend(["--worker-archive", str(archive)])
    done = subprocess.run(cmd, cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    lines = [line for line in done.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"exact-owner CCtx worker emitted no JSON for {mode}")
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]
    build_rows = []
    context_rows = []
    for round_index in range(ROUNDS):
        archive = work_root / "archives" / f"round-{round_index}.cmpct"
        archive.parent.mkdir(parents=True, exist_ok=True)
        if round_index % 2 == 0:
            build_rows.append(run_worker("build", source, archive))
            context_rows.append(run_worker("context", source))
        else:
            context_rows.append(run_worker("context", source))
            build_rows.append(run_worker("build", source, archive))

    identities = {(r["archive_bytes"], r["archive_sha256"], r["tree_sha256"], r["owner_module"]) for r in build_rows}
    exact_identity = len(identities) == 1 and all(r["owner_module"] == EXPECTED_MODULE for r in context_rows)
    tree_ids = {r["tree_sha256"] for r in build_rows} | {r["tree_sha256"] for r in context_rows}
    exact_tree = len(tree_ids) == 1
    max_cctx_per_round = [max(int(a["peak_reported_cctx_bytes"]) for a in row["anchors"]) for row in context_rows]
    max_cctx = float(statistics.median(max_cctx_per_round))
    inc_kib = float(statistics.median(float(r["incremental_peak_rss_kib"]) for r in build_rows))
    peak_kib = float(statistics.median(float(r["peak_rss_kib"]) for r in build_rows))
    share = max_cctx / max(1.0, inc_kib * 1024.0)
    if share >= 0.50:
        decision = "CCTX_MATERIAL_OWNER_SUPPORTED"
    elif share < 0.20:
        decision = "CCTX_RETIRED_AS_PRIMARY_EXACT_OWNER_ALLOCATION"
    else:
        decision = "CCTX_ATTRIBUTION_AMBIGUOUS"
    valid = bool(exact_identity and exact_tree and all(r["anchors"] for r in context_rows))
    return {
        "schema": "cmpct-v030-prefixgraph-exact-owner-cctx-memory-v2",
        "source_commit": source_commit(),
        "target": list(TARGET),
        "rounds": ROUNDS,
        "build_rows": build_rows,
        "context_rows": context_rows,
        "summary": {
            "median_exact_owner_peak_rss_kib": peak_kib,
            "median_exact_owner_incremental_peak_rss_kib": inc_kib,
            "median_max_reported_single_cctx_bytes": max_cctx,
            "max_cctx_share_of_exact_owner_incremental_rss": share,
            "decision": decision,
        },
        "gate": {"exact_owner_identity": exact_identity, "exact_tree_identity": exact_tree, "experiment_valid": valid},
        "contract": {
            "support_threshold": 0.50,
            "retire_threshold": 0.20,
            "production_change": False,
            "compressor_parameters_changed": False,
            "candidate_set_changed": False,
            "release_credit": False,
        },
        "release_credit": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-exact-owner-cctx-v2-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-exact-owner-cctx-v2.json"))
    parser.add_argument("--worker-mode", choices=("build", "context"))
    parser.add_argument("--worker-source", type=Path)
    parser.add_argument("--worker-archive", type=Path)
    args = parser.parse_args()
    if args.worker_mode:
        if args.worker_source is None:
            raise SystemExit("--worker-source is required")
        if args.worker_mode == "build":
            if args.worker_archive is None:
                raise SystemExit("--worker-archive is required for build")
            result = exact_build(args.worker_source, args.worker_archive)
        else:
            result = profile_contexts(args.worker_source)
        print(json.dumps(result, sort_keys=True), flush=True)
        return
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("exact-owner PrefixGraph CCtx v2 identity gate failed")


if __name__ == "__main__":
    main()
