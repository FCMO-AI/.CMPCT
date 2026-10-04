from __future__ import annotations

"""Frozen R36 project-owned Condition.wait attribution diagnostic.

Normative freeze:
``docs/v030-rnd/R36_REGENERABLE_DEFLATE_PROJECT_WAIT_OWNER_PREREG.md``.
Diagnostic only; no product or release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import threading
import time

from benchmarks import v030_r32_regenerable_deflate_output_dead_zstd_elision as R32
from benchmarks import v030_r34_regenerable_deflate_same_run_phase_attribution as R34
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "cmpct-v030-r36-regenerable-deflate-project-wait-owner-v1"
REPETITIONS = 3
ARMS = R34.ARMS
EXCLUDED_ROOTS = {"benchmarks", "tests", "docs", ".github"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _project_frame_from_stack(frame) -> tuple[str, int] | None:
    """Return nearest production repository frame, excluding diagnostic/test surfaces."""
    cursor = frame
    while cursor is not None:
        filename = Path(cursor.f_code.co_filename)
        try:
            rel = filename.resolve().relative_to(ROOT.resolve())
        except (ValueError, OSError):
            cursor = cursor.f_back
            continue
        if rel.parts and rel.parts[0] not in EXCLUDED_ROOTS:
            return f"{rel.as_posix()}:{cursor.f_code.co_name}", int(cursor.f_lineno)
        cursor = cursor.f_back
    return None


def _worker(arm: str, source: Path, archive: Path) -> dict:
    wait_rows: dict[str, dict] = {}
    wait_calls = 0
    wait_elapsed_s = 0.0
    original_wait = threading.Condition.wait
    restored = False

    def measured_wait(condition, timeout=None):
        nonlocal wait_calls, wait_elapsed_s
        # f_back is the caller of this wrapper. Walk outward from there so the
        # diagnostic frame itself can never become the attributed owner.
        owner = _project_frame_from_stack(sys._getframe(1))
        signature, line = owner if owner is not None else ("<no-project-frame>", -1)
        started = time.perf_counter()
        try:
            return original_wait(condition, timeout)
        finally:
            elapsed = time.perf_counter() - started
            wait_calls += 1
            wait_elapsed_s += elapsed
            row = wait_rows.setdefault(signature, {"calls": 0, "elapsed_s": 0.0, "line_numbers": set()})
            row["calls"] += 1
            row["elapsed_s"] += elapsed
            if line >= 0:
                row["line_numbers"].add(line)

    archive.parent.mkdir(parents=True, exist_ok=True)
    threading.Condition.wait = measured_wait
    started = time.perf_counter()
    try:
        R32._build_arm(arm, source, archive)
    finally:
        threading.Condition.wait = original_wait
        restored = threading.Condition.wait is original_wait
    wall_s = time.perf_counter() - started

    if not restored:
        raise RuntimeError("R36 failed to restore threading.Condition.wait")

    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok"):
        raise RuntimeError(f"R36 {arm} strong verification failed: {verified!r}")
    tree = PRODUCT.treehash(source)
    if verified.get("tree_sha256") != tree:
        raise RuntimeError(f"R36 {arm} product-tree mismatch")

    owners = {}
    for signature, row in sorted(wait_rows.items()):
        owners[signature] = {
            "calls": int(row["calls"]),
            "elapsed_s": float(row["elapsed_s"]),
            "line_numbers": sorted(int(x) for x in row["line_numbers"]),
        }

    return {
        "arm": arm,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": sha256_file(archive),
        "tree_sha256": tree,
        "strong_verify_ok": True,
        "wall_s": wall_s,
        "condition_wait_calls": int(wait_calls),
        "condition_wait_elapsed_s": float(wait_elapsed_s),
        "wait_wrapper_restored": restored,
        "project_wait_owners": owners,
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
        raise RuntimeError(f"R36 worker emitted no result: {completed.stdout!r} {completed.stderr!r}")
    return json.loads(output.read_text())


def _stable_identity(reps: list[dict]) -> tuple[bool, tuple[int, str]]:
    pairs = {(int(row["archive_bytes"]), str(row["archive_sha256"])) for row in reps}
    return (len(pairs) == 1, next(iter(pairs)) if len(pairs) == 1 else (-1, ""))


def _median_owners(reps: list[dict]) -> dict[str, dict]:
    signatures = sorted({sig for row in reps for sig in row["project_wait_owners"]})
    out = {}
    for signature in signatures:
        vals = []
        lines = set()
        for row in reps:
            found = row["project_wait_owners"].get(signature, {"calls": 0, "elapsed_s": 0.0, "line_numbers": []})
            vals.append(found)
            lines.update(found.get("line_numbers", []))
        out[signature] = {
            "calls": int(statistics.median(v["calls"] for v in vals)),
            "elapsed_s": float(statistics.median(v["elapsed_s"] for v in vals)),
            "line_numbers": sorted(int(x) for x in lines),
        }
    return out


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    full, nested, identity = R34.build_sources(work_root)
    result = {
        "schema": SCHEMA,
        "status": "diagnostic-only-no-release-credit",
        "evidence_head": os.environ.get("CMPCT_EVIDENCE_HEAD", ""),
        "parent_r35_result": "R35_REGENERABLE_DEFLATE_LOCK_CALLER_ATTRIBUTION_RESULT.md",
        "identity": identity,
        "repetitions": REPETITIONS,
        "targets": {},
    }
    identity_ok = True
    instrumentation_ok = True

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
            target["arms"][arm] = {
                "repetitions": reps,
                "median_wall_s": float(statistics.median(row["wall_s"] for row in reps)),
                "median_condition_wait_calls": int(statistics.median(row["condition_wait_calls"] for row in reps)),
                "median_condition_wait_elapsed_s": float(statistics.median(row["condition_wait_elapsed_s"] for row in reps)),
                "deterministic_within_run": stable,
                "identity_pair": {"archive_bytes": pair[0], "archive_sha256": pair[1]},
                "median_project_wait_owners": _median_owners(reps),
            }
            identity_ok = identity_ok and stable and all(row["strong_verify_ok"] for row in reps)
            instrumentation_ok = instrumentation_ok and all(row["wait_wrapper_restored"] and row["condition_wait_calls"] > 0 for row in reps)

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
    result["wait_instrumentation_ok"] = instrumentation_ok
    if not identity_ok:
        result["decision"] = "SUBSTRATE_OR_SAME_RUN_IDENTITY_FAILURE"
        result["localized_project_owners"] = []
        return result
    if not instrumentation_ok:
        result["decision"] = "WAIT_INSTRUMENTATION_UNRESOLVED"
        result["localized_project_owners"] = []
        return result

    def deltas(target_name: str) -> dict[str, dict]:
        arms = result["targets"][target_name]["arms"]
        base = arms["release-all-exact"]["median_project_wait_owners"]
        cand = arms["no-ordinary-zstd"]["median_project_wait_owners"]
        out = {}
        for sig in sorted(set(base) | set(cand)):
            b = base.get(sig, {"elapsed_s": 0.0, "calls": 0, "line_numbers": []})
            c = cand.get(sig, {"elapsed_s": 0.0, "calls": 0, "line_numbers": []})
            out[sig] = {
                "wait_time_delta_s": float(c["elapsed_s"] - b["elapsed_s"]),
                "call_delta": int(c["calls"] - b["calls"]),
                "release_wait_s": float(b["elapsed_s"]),
                "candidate_wait_s": float(c["elapsed_s"]),
                "line_numbers": sorted(set(b.get("line_numbers", [])) | set(c.get("line_numbers", []))),
            }
        return out

    full_delta = deltas("full-backups")
    nested_delta = deltas("nested-only")
    result["project_owner_deltas"] = {"full-backups": full_delta, "nested-only": nested_delta}
    localized = []
    for sig, nested_row in nested_delta.items():
        if sig == "<no-project-frame>":
            continue
        full_row = full_delta.get(sig)
        if full_row and nested_row["wait_time_delta_s"] >= 0.010 and full_row["wait_time_delta_s"] > 0:
            localized.append({
                "signature": sig,
                "nested_wait_time_delta_s": nested_row["wait_time_delta_s"],
                "full_wait_time_delta_s": full_row["wait_time_delta_s"],
                "nested_call_delta": nested_row["call_delta"],
                "full_call_delta": full_row["call_delta"],
                "line_numbers": sorted(set(nested_row["line_numbers"]) | set(full_row["line_numbers"])),
            })
    localized.sort(key=lambda row: (-row["nested_wait_time_delta_s"], row["signature"]))
    result["localized_project_owners"] = localized
    if localized:
        result["decision"] = "PROJECT_WAIT_OWNER_LOCALIZED"
    else:
        no_project = nested_delta.get("<no-project-frame>", {"wait_time_delta_s": 0.0})
        full_no_project = full_delta.get("<no-project-frame>", {"wait_time_delta_s": 0.0})
        if no_project["wait_time_delta_s"] >= 0.010 and full_no_project["wait_time_delta_s"] > 0:
            result["decision"] = "PROJECT_WAIT_OWNER_UNRESOLVED"
        else:
            result["decision"] = "PROJECT_WAIT_OWNER_DISTRIBUTED_OR_BELOW_FLOOR"
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
        row = _worker(args.worker_arm, args.source, args.archive)
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
