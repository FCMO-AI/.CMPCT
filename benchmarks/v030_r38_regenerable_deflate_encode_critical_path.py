from __future__ import annotations

"""Frozen R38 per-candidate encode critical-path attribution.

Normative preregistration:
``docs/v030-rnd/R38_REGENERABLE_DEFLATE_ENCODE_CRITICAL_PATH_PREREG.md``.

Diagnostic only. This instrument preserves the inherited ThreadPoolExecutor.map
implementation and ordered consumer semantics; it only wraps the submitted
encode callable to record task-level timing and representation facts.
"""

import argparse
import concurrent.futures
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

from benchmarks import v030_r32_regenerable_deflate_output_dead_zstd_elision as R32
from benchmarks import v030_r34_regenerable_deflate_same_run_phase_attribution as R34
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "cmpct-v030-r38-regenerable-deflate-encode-critical-path-v1"
REPETITIONS = 3
MAX_LOCALITY = 8.0
ARMS = ("release-all-exact", "no-ordinary-zstd")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _zip_members(root: Path) -> list[str]:
    out: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink() and path.suffix.lower() in {".zip", ".whl"}:
            out.append(path.relative_to(root).as_posix())
    return out


def _worker(arm: str, source: Path, archive: Path) -> dict:
    from benchmarks.v030_perf_worker_canonical import _observed_product_member

    archive.parent.mkdir(parents=True, exist_ok=True)
    original_map = concurrent.futures.ThreadPoolExecutor.map
    instrumented_map_calls = 0
    task_rows: list[dict] = []

    def instrumented_map(executor, fn, *iterables, timeout=None, chunksize=1):
        nonlocal instrumented_map_calls
        instrumented_map_calls += 1
        if len(iterables) != 1:
            raise RuntimeError(f"R38 expected one encode iterable, observed {len(iterables)}")
        if instrumented_map_calls != 1:
            raise RuntimeError(f"R38 expected one Builder map call, observed {instrumented_map_calls}")

        def wrapped(item):
            h, candidate = item
            started = time.perf_counter()
            result = fn(item)
            ended = time.perf_counter()
            rh, rc, codec, comp, meta = result
            if rh != h or rc is not candidate:
                raise RuntimeError("R38 encode wrapper observed changed candidate identity")
            task_rows.append(
                {
                    "candidate_key": bytes(h).hex(),
                    "raw_bytes": len(candidate.raw),
                    "hints": sorted(candidate.hints),
                    "deflate_alternative_count": len(candidate.deflates),
                    "start_abs_s": started,
                    "end_abs_s": ended,
                    "elapsed_s": ended - started,
                    "result_codec": int(codec),
                    "result_compressed_metadata_bytes": len(comp) + len(meta),
                }
            )
            return result

        return original_map(
            executor,
            wrapped,
            *iterables,
            timeout=timeout,
            chunksize=chunksize,
        )

    concurrent.futures.ThreadPoolExecutor.map = instrumented_map
    started = time.perf_counter()
    try:
        _stats, effective, retention, specialized = R32._build_arm(arm, source, archive)
    finally:
        concurrent.futures.ThreadPoolExecutor.map = original_map
    build_wall_s = time.perf_counter() - started
    peak_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    if instrumented_map_calls != 1:
        raise RuntimeError(f"R38 expected exactly one Builder map call, observed {instrumented_map_calls}")
    if not task_rows:
        raise RuntimeError("R38 observed no encode tasks")

    earliest = min(row["start_abs_s"] for row in task_rows)
    normalized_rows = []
    seen_keys: set[str] = set()
    for row in task_rows:
        key = row["candidate_key"]
        if key in seen_keys:
            raise RuntimeError(f"R38 duplicate candidate key in one build: {key}")
        seen_keys.add(key)
        normalized_rows.append(
            {
                "candidate_key": key,
                "raw_bytes": row["raw_bytes"],
                "hints": row["hints"],
                "deflate_alternative_count": row["deflate_alternative_count"],
                "start_s": row["start_abs_s"] - earliest,
                "end_s": row["end_abs_s"] - earliest,
                "elapsed_s": row["elapsed_s"],
                "result_codec": row["result_codec"],
                "result_compressed_metadata_bytes": row["result_compressed_metadata_bytes"],
            }
        )
    normalized_rows.sort(key=lambda row: row["candidate_key"])
    encode_makespan_s = max(row["end_s"] for row in normalized_rows)

    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok"):
        raise RuntimeError(f"R38 {arm} strong verification failed: {verified!r}")
    tree = PRODUCT.treehash(source)
    if verified.get("tree_sha256") != tree:
        raise RuntimeError(f"R38 {arm} product-tree mismatch")

    virtual_members = []
    for member in _zip_members(source):
        raw, locality = _observed_product_member(PRODUCT, archive, member)
        decoded = locality.get("decoded_context_bytes")
        if decoded is None:
            raise RuntimeError(f"R38 {arm} missing decoded-context accounting for {member}")
        amp = float(locality["max_member_read_amplification"])
        virtual_members.append(
            {
                "member": member,
                "member_bytes": len(raw),
                "decoded_context_bytes": int(decoded),
                "decoded_context_amplification": amp,
                "locality_within_8x": amp <= MAX_LOCALITY,
            }
        )
    if not virtual_members:
        raise RuntimeError(f"R38 {arm} target contains no virtual ZIP/WHL member")

    return {
        "arm": arm,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256_file(archive),
        "tree_sha256": tree,
        "strong_verify_ok": True,
        "build_wall_s": build_wall_s,
        "build_peak_rss_kib": peak_rss_kib,
        "instrumented_map_calls": instrumented_map_calls,
        "encode_task_count": len(normalized_rows),
        "encode_makespan_s": encode_makespan_s,
        "encode_tasks": normalized_rows,
        "effective": effective,
        "retention": retention,
        "specialized": specialized,
        "max_virtual_member_amplification": max(row["decoded_context_amplification"] for row in virtual_members),
        "locality_within_8x": all(row["locality_within_8x"] for row in virtual_members),
    }


def _fresh_worker(arm: str, source: Path, archive: Path, output: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-arm",
            arm,
            "--source",
            str(source),
            "--archive",
            str(archive),
            "--worker-output",
            str(output),
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    if not output.is_file():
        raise RuntimeError(f"R38 worker emitted no result: {completed.stdout!r} {completed.stderr!r}")
    return json.loads(output.read_text())


def _arm_summary(reps: list[dict]) -> dict:
    identities = {(row["archive_bytes"], row["archive_sha256"]) for row in reps}
    task_key_sets = [tuple(row["candidate_key"] for row in rep["encode_tasks"]) for rep in reps]
    task_metadata_by_key: dict[str, tuple] = {}
    metadata_consistent = True
    for rep in reps:
        for row in rep["encode_tasks"]:
            meta = (
                row["raw_bytes"],
                tuple(row["hints"]),
                row["deflate_alternative_count"],
                row["result_codec"],
                row["result_compressed_metadata_bytes"],
            )
            previous = task_metadata_by_key.setdefault(row["candidate_key"], meta)
            metadata_consistent = metadata_consistent and previous == meta

    per_key = {}
    if len(set(task_key_sets)) == 1 and metadata_consistent:
        for key in task_key_sets[0]:
            rows = [
                next(task for task in rep["encode_tasks"] if task["candidate_key"] == key)
                for rep in reps
            ]
            per_key[key] = {
                "candidate_key": key,
                "raw_bytes": rows[0]["raw_bytes"],
                "hints": rows[0]["hints"],
                "deflate_alternative_count": rows[0]["deflate_alternative_count"],
                "result_codec": rows[0]["result_codec"],
                "result_compressed_metadata_bytes": rows[0]["result_compressed_metadata_bytes"],
                "median_elapsed_s": float(statistics.median(row["elapsed_s"] for row in rows)),
            }

    return {
        "deterministic_within_run": len(identities) == 1,
        "archive_bytes": int(statistics.median(row["archive_bytes"] for row in reps)),
        "archive_sha256": next(iter(identities))[1] if len(identities) == 1 else "",
        "build_wall_s": float(statistics.median(row["build_wall_s"] for row in reps)),
        "build_peak_rss_kib": int(statistics.median(row["build_peak_rss_kib"] for row in reps)),
        "instrumented_map_calls": [int(row["instrumented_map_calls"]) for row in reps],
        "task_keys_deterministic": len(set(task_key_sets)) == 1,
        "task_metadata_deterministic": metadata_consistent,
        "encode_task_count": int(statistics.median(row["encode_task_count"] for row in reps)),
        "median_encode_makespan_s": float(statistics.median(row["encode_makespan_s"] for row in reps)),
        "per_key": per_key,
        "strong_verify_ok": all(row["strong_verify_ok"] for row in reps),
        "locality_within_8x": all(row["locality_within_8x"] for row in reps),
        "max_virtual_member_amplification": max(row["max_virtual_member_amplification"] for row in reps),
    }


def _positive_excess(release: dict, candidate: dict) -> list[dict]:
    rows = []
    release_keys = release["per_key"]
    candidate_keys = candidate["per_key"]
    for key in sorted(set(release_keys) | set(candidate_keys)):
        c = candidate_keys.get(key)
        r = release_keys.get(key)
        if c is None:
            continue
        candidate_elapsed = float(c["median_elapsed_s"])
        release_elapsed = float(r["median_elapsed_s"]) if r is not None else 0.0
        delta = candidate_elapsed - release_elapsed
        if delta <= 0:
            continue
        rows.append(
            {
                "candidate_key": key,
                "raw_bytes": c["raw_bytes"],
                "hints": c["hints"],
                "deflate_alternative_count": c["deflate_alternative_count"],
                "result_codec": c["result_codec"],
                "result_compressed_metadata_bytes": c["result_compressed_metadata_bytes"],
                "candidate_median_elapsed_s": candidate_elapsed,
                "release_median_elapsed_s": release_elapsed,
                "positive_delta_s": delta,
                "candidate_only": r is None,
            }
        )
    rows.sort(key=lambda row: (-row["positive_delta_s"], row["candidate_key"]))
    total = sum(row["positive_delta_s"] for row in rows)
    for row in rows:
        row["share_of_summed_positive_excess"] = row["positive_delta_s"] / total if total > 0 else 0.0
    return rows


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    full, nested, identity = R34.build_sources(work_root)
    result = {
        "schema": SCHEMA,
        "status": "diagnostic-only-no-release-credit",
        "evidence_head": os.environ.get("CMPCT_EVIDENCE_HEAD", ""),
        "parent_r37_result": "R37_REGENERABLE_DEFLATE_WAIT_ONCE_BUILDER_RESULT.md",
        "identity": identity,
        "repetitions": REPETITIONS,
        "targets": {},
    }

    valid = True
    for target_name, source in {"full-backups": full, "nested-only": nested}.items():
        target = {"arms": {}}
        for arm in ARMS:
            reps = []
            for rep in range(REPETITIONS):
                archive = work_root / "archives" / target_name / arm / f"{rep}.cmpct"
                output = work_root / "workers" / target_name / arm / f"{rep}.json"
                output.parent.mkdir(parents=True, exist_ok=True)
                reps.append(_fresh_worker(arm, source, archive, output))
            target["arms"][arm] = {"repetitions": reps, "median": _arm_summary(reps)}

        release = target["arms"]["release-all-exact"]["median"]
        candidate = target["arms"]["no-ordinary-zstd"]["median"]
        identity_ok = (
            release["deterministic_within_run"]
            and candidate["deterministic_within_run"]
            and release["strong_verify_ok"]
            and candidate["strong_verify_ok"]
            and release["instrumented_map_calls"] == [1, 1, 1]
            and candidate["instrumented_map_calls"] == [1, 1, 1]
            and release["task_keys_deterministic"]
            and candidate["task_keys_deterministic"]
            and release["task_metadata_deterministic"]
            and candidate["task_metadata_deterministic"]
            and release["per_key"]
            and candidate["per_key"]
            and candidate["archive_bytes"] < release["archive_bytes"]
            and release["locality_within_8x"]
            and candidate["locality_within_8x"]
        )
        target["identity_and_instrument_ok"] = bool(identity_ok)
        target["positive_excess"] = _positive_excess(release, candidate) if identity_ok else []
        target["summed_positive_excess_s"] = sum(
            row["positive_delta_s"] for row in target["positive_excess"]
        )
        target["dominant_positive_excess"] = target["positive_excess"][0] if target["positive_excess"] else None
        valid = valid and bool(identity_ok)
        result["targets"][target_name] = target

    if not valid:
        decision = "SUBSTRATE_OR_INSTRUMENT_FAILURE"
    else:
        full_target = result["targets"]["full-backups"]
        nested_target = result["targets"]["nested-only"]
        if full_target["summed_positive_excess_s"] <= 0 or nested_target["summed_positive_excess_s"] <= 0:
            decision = "NO_ENCODE_WORK_EXCESS"
        else:
            full_dom = full_target["dominant_positive_excess"]
            nested_dom = nested_target["dominant_positive_excess"]
            localized = (
                full_dom is not None
                and nested_dom is not None
                and full_dom["candidate_key"] == nested_dom["candidate_key"]
                and full_dom["positive_delta_s"] > 0
                and nested_dom["positive_delta_s"] >= 0.010
                and nested_dom["share_of_summed_positive_excess"] >= 0.50
            )
            decision = "CRITICAL_ENCODE_OWNER_LOCALIZED" if localized else "ENCODE_FAMILY_DISTRIBUTED"

    result["decision"] = decision
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--worker-arm", choices=ARMS)
    ap.add_argument("--source", type=Path)
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--worker-output", type=Path)
    args = ap.parse_args()
    if args.worker_arm:
        if args.source is None or args.archive is None or args.worker_output is None:
            ap.error("worker mode requires --source --archive --worker-output")
        row = _worker(args.worker_arm, args.source, args.archive)
        args.worker_output.parent.mkdir(parents=True, exist_ok=True)
        args.worker_output.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
        return
    if args.work_root is None or args.output is None:
        ap.error("parent mode requires --work-root --output")
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
