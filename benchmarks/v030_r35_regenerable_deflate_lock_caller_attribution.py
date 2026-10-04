from __future__ import annotations

"""Frozen R35 caller-level attribution for R34's localized lock phase.

Normative freeze:
``docs/v030-rnd/R35_REGENERABLE_DEFLATE_LOCK_CALLER_ATTRIBUTION_PREREG.md``.
Diagnostic only; no product or release credit.
"""

import argparse
import cProfile
import json
import os
from pathlib import Path
import pstats
import shutil
import statistics
import subprocess
import sys
import time

from benchmarks import v030_r32_regenerable_deflate_output_dead_zstd_elision as R32
from benchmarks import v030_r34_regenerable_deflate_same_run_phase_attribution as R34
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "cmpct-v030-r35-regenerable-deflate-lock-caller-attribution-v1"
REPETITIONS = 3
ARMS = R34.ARMS
LOCK_NAME = "<method 'acquire' of '_thread.lock' objects>"


def _signature(key: tuple[str, int, str]) -> str:
    filename, line, name = key
    return f"{Path(filename).name}:{line}:{name}"


def _caller_value(value) -> dict:
    """Normalize the pstats caller tuple without assuming a Python minor-version alias."""
    if not isinstance(value, tuple):
        raise TypeError(f"unexpected pstats caller value: {value!r}")
    if len(value) == 4:
        cc, nc, tt, ct = value
    elif len(value) == 3:
        nc, tt, ct = value
        cc = nc
    else:
        raise TypeError(f"unexpected pstats caller tuple width {len(value)}: {value!r}")
    return {
        "primitive_calls": int(cc),
        "calls": int(nc),
        "internal_s": float(tt),
        "cumulative_s": float(ct),
    }


def _profile_worker(arm: str, source: Path, archive: Path) -> dict:
    profiler = cProfile.Profile()
    started = time.perf_counter()
    profiler.runcall(R32._build_arm, arm, source, archive)
    wall_s = time.perf_counter() - started
    stats = pstats.Stats(profiler)

    lock_key = next(
        (key for key in stats.stats if key[0] == "~" and key[1] == 0 and key[2] == LOCK_NAME),
        None,
    )
    lock = None
    if lock_key is not None:
        cc, nc, tt, ct, callers = stats.stats[lock_key]
        caller_rows = []
        for caller_key, value in callers.items():
            row = _caller_value(value)
            row["signature"] = _signature(caller_key)
            caller_rows.append(row)
        caller_rows.sort(key=lambda row: (-row["cumulative_s"], row["signature"]))
        lock = {
            "signature": _signature(lock_key),
            "primitive_calls": int(cc),
            "calls": int(nc),
            "internal_s": float(tt),
            "cumulative_s": float(ct),
            "callers": caller_rows,
        }

    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok"):
        raise RuntimeError(f"R35 {arm} strong verification failed: {verified!r}")
    tree = PRODUCT.treehash(source)
    if verified.get("tree_sha256") != tree:
        raise RuntimeError(f"R35 {arm} product-tree mismatch")

    return {
        "arm": arm,
        "wall_s": wall_s,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": R34.sha256_file(archive),
        "tree_sha256": tree,
        "strong_verify_ok": True,
        "lock": lock,
    }


def _fresh_worker(arm: str, source: Path, archive: Path, output: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-arm", arm,
            "--source", str(source),
            "--archive", str(archive),
            "--worker-output", str(output),
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    if not output.is_file():
        raise RuntimeError(f"R35 worker emitted no result: {completed.stdout!r} {completed.stderr!r}")
    return json.loads(output.read_text())


def _stable_identity(reps: list[dict]) -> tuple[bool, tuple[int, str]]:
    pairs = {(int(row["archive_bytes"]), str(row["archive_sha256"])) for row in reps}
    return (len(pairs) == 1, next(iter(pairs)) if len(pairs) == 1 else (-1, ""))


def _median_callers(reps: list[dict]) -> tuple[bool, dict[str, dict], dict]:
    if any(row.get("lock") is None for row in reps):
        return False, {}, {}
    signatures = sorted({c["signature"] for row in reps for c in row["lock"]["callers"]})
    callers = {}
    for sig in signatures:
        vals = []
        for row in reps:
            found = next((c for c in row["lock"]["callers"] if c["signature"] == sig), None)
            vals.append(found or {"calls": 0, "primitive_calls": 0, "internal_s": 0.0, "cumulative_s": 0.0})
        callers[sig] = {
            "calls": int(statistics.median(v["calls"] for v in vals)),
            "primitive_calls": int(statistics.median(v["primitive_calls"] for v in vals)),
            "internal_s": float(statistics.median(v["internal_s"] for v in vals)),
            "cumulative_s": float(statistics.median(v["cumulative_s"] for v in vals)),
        }
    lock_summary = {
        "calls": int(statistics.median(row["lock"]["calls"] for row in reps)),
        "internal_s": float(statistics.median(row["lock"]["internal_s"] for row in reps)),
        "cumulative_s": float(statistics.median(row["lock"]["cumulative_s"] for row in reps)),
    }
    return True, callers, lock_summary


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    full, nested, identity = R34.build_sources(work_root)
    result = {
        "schema": SCHEMA,
        "status": "diagnostic-only-no-release-credit",
        "evidence_head": os.environ.get("CMPCT_EVIDENCE_HEAD", ""),
        "parent_r32_head": "0b1f3cd653f0e2489964b93cdd19fa8324adda2e",
        "parent_r34_result_head": "7c1bbaf272ac286180c6876d996c18d3d04b9748",
        "identity": identity,
        "repetitions": REPETITIONS,
        "targets": {},
    }
    identity_ok = True
    callers_usable = True

    for target_name, source in {"full-backups": full, "nested-only": nested}.items():
        target = {"arms": {}}
        for arm in ARMS:
            reps = []
            for rep in range(REPETITIONS):
                archive = work_root / "archives" / target_name / arm / f"{rep}.cmpct"
                output = work_root / "workers" / target_name / arm / f"{rep}.json"
                archive.parent.mkdir(parents=True, exist_ok=True)
                output.parent.mkdir(parents=True, exist_ok=True)
                reps.append(_fresh_worker(arm, source, archive, output))
            stable, pair = _stable_identity(reps)
            usable, callers, lock_summary = _median_callers(reps)
            target["arms"][arm] = {
                "repetitions": reps,
                "median_wall_s": float(statistics.median(row["wall_s"] for row in reps)),
                "deterministic_within_run": stable,
                "identity_pair": {"archive_bytes": pair[0], "archive_sha256": pair[1]},
                "lock_callers_usable": usable,
                "median_lock": lock_summary,
                "median_callers": callers,
            }
            identity_ok = identity_ok and stable and all(row["strong_verify_ok"] for row in reps)
            callers_usable = callers_usable and usable

        release = target["arms"]["release-all-exact"]
        fullsearch = target["arms"]["full-search"]
        candidate = target["arms"]["no-ordinary-zstd"]
        target["full_search_no_zstd_byte_identity"] = fullsearch["identity_pair"] == candidate["identity_pair"]
        target["candidate_strictly_smaller_than_release"] = (
            candidate["identity_pair"]["archive_bytes"] >= 0
            and candidate["identity_pair"]["archive_bytes"] < release["identity_pair"]["archive_bytes"]
        )
        identity_ok = identity_ok and target["full_search_no_zstd_byte_identity"] and target["candidate_strictly_smaller_than_release"]
        result["targets"][target_name] = target

    result["same_run_identity_ok"] = identity_ok
    result["caller_data_usable"] = callers_usable
    if not identity_ok:
        result["decision"] = "SUBSTRATE_OR_SAME_RUN_IDENTITY_FAILURE"
        result["localized_callers"] = []
        return result
    if not callers_usable:
        result["decision"] = "LOCK_CALLER_UNRESOLVED"
        result["localized_callers"] = []
        return result

    def deltas(target_name: str) -> dict[str, dict]:
        arms = result["targets"][target_name]["arms"]
        base = arms["release-all-exact"]["median_callers"]
        cand = arms["no-ordinary-zstd"]["median_callers"]
        out = {}
        for sig in sorted(set(base) | set(cand)):
            b = base.get(sig, {"cumulative_s": 0.0, "calls": 0})
            c = cand.get(sig, {"cumulative_s": 0.0, "calls": 0})
            out[sig] = {
                "lock_time_delta_s": float(c["cumulative_s"] - b["cumulative_s"]),
                "call_delta": int(c["calls"] - b["calls"]),
                "release_lock_time_s": float(b["cumulative_s"]),
                "candidate_lock_time_s": float(c["cumulative_s"]),
            }
        return out

    full_delta = deltas("full-backups")
    nested_delta = deltas("nested-only")
    result["caller_deltas"] = {"full-backups": full_delta, "nested-only": nested_delta}
    localized = []
    for sig, nested_row in nested_delta.items():
        full_row = full_delta.get(sig)
        if full_row and nested_row["lock_time_delta_s"] >= 0.010 and full_row["lock_time_delta_s"] > 0:
            localized.append({
                "signature": sig,
                "nested_lock_time_delta_s": nested_row["lock_time_delta_s"],
                "full_lock_time_delta_s": full_row["lock_time_delta_s"],
                "nested_call_delta": nested_row["call_delta"],
                "full_call_delta": full_row["call_delta"],
            })
    localized.sort(key=lambda row: (-row["nested_lock_time_delta_s"], row["signature"]))
    result["localized_callers"] = localized
    result["decision"] = "LOCK_CALLER_LOCALIZED" if localized else "LOCK_CALLER_DISTRIBUTED_OR_BELOW_FLOOR"
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
    if args.worker_arm is not None:
        if args.source is None or args.archive is None or args.worker_output is None:
            ap.error("worker mode requires --source, --archive and --worker-output")
        row = _profile_worker(args.worker_arm, args.source, args.archive)
        args.worker_output.parent.mkdir(parents=True, exist_ok=True)
        args.worker_output.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
        return
    if args.work_root is None or args.output is None:
        ap.error("parent mode requires --work-root and --output")
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
