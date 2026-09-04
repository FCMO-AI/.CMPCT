from __future__ import annotations

"""Frozen R37 wait-once scheduling-boundary Builder.

Normative freeze:
``docs/v030-rnd/R37_REGENERABLE_DEFLATE_WAIT_ONCE_BUILDER_PREREG.md``.
Diagnostic only until the frozen terminal law authorizes productization.
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
SCHEMA = "cmpct-v030-r37-regenerable-deflate-wait-once-builder-v1"
REPETITIONS = 3
MAX_LOCALITY = 8.0
ARMS = ("release-all-exact", "candidate-map-control", "candidate-wait-once")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _zip_members(root: Path) -> list[str]:
    out = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink() and path.suffix.lower() in {".zip", ".whl"}:
            out.append(path.relative_to(root).as_posix())
    return out


def _material_runtime_regression(base_s: float, candidate_s: float) -> bool:
    delta = candidate_s - base_s
    return delta > 0.003 and (delta / base_s if base_s > 0 else float("inf")) > 0.05


def _worker(arm: str, source: Path, archive: Path) -> dict:
    from benchmarks.v030_perf_worker_canonical import _observed_product_member

    archive.parent.mkdir(parents=True, exist_ok=True)
    patched_map_calls = 0
    original_map = concurrent.futures.ThreadPoolExecutor.map

    def wait_once_map(executor, fn, *iterables, timeout=None, chunksize=1):
        nonlocal patched_map_calls
        patched_map_calls += 1
        if len(iterables) != 1 or timeout is not None or chunksize != 1:
            raise RuntimeError("R37 observed an unexpected ThreadPoolExecutor.map shape")
        items = list(iterables[0])
        futures = [executor.submit(fn, item) for item in items]
        concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)
        return iter(future.result() for future in futures)

    inherited_arm = "release-all-exact" if arm == "release-all-exact" else "no-ordinary-zstd"
    if arm == "candidate-wait-once":
        concurrent.futures.ThreadPoolExecutor.map = wait_once_map
    started = time.perf_counter()
    try:
        R32._build_arm(inherited_arm, source, archive)
    finally:
        concurrent.futures.ThreadPoolExecutor.map = original_map
    wall_s = time.perf_counter() - started
    peak_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    if arm == "candidate-wait-once" and patched_map_calls != 1:
        raise RuntimeError(f"R37 expected exactly one patched Builder map call, observed {patched_map_calls}")
    if arm != "candidate-wait-once" and patched_map_calls != 0:
        raise RuntimeError("R37 control arm unexpectedly patched scheduling")

    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok"):
        raise RuntimeError(f"R37 {arm} strong verification failed: {verified!r}")
    tree = PRODUCT.treehash(source)
    if verified.get("tree_sha256") != tree:
        raise RuntimeError(f"R37 {arm} product-tree mismatch")

    virtual_members = []
    for member in _zip_members(source):
        raw, locality = _observed_product_member(PRODUCT, archive, member)
        decoded = locality.get("decoded_context_bytes")
        if decoded is None:
            raise RuntimeError(f"R37 {arm} missing decoded-context accounting for {member}")
        amp = float(locality["max_member_read_amplification"])
        virtual_members.append({
            "member": member,
            "member_bytes": len(raw),
            "decoded_context_bytes": int(decoded),
            "decoded_context_amplification": amp,
            "locality_within_8x": amp <= MAX_LOCALITY,
        })
    if not virtual_members:
        raise RuntimeError(f"R37 {arm} target contains no virtual ZIP/WHL member")

    return {
        "arm": arm,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256_file(archive),
        "tree_sha256": tree,
        "strong_verify_ok": True,
        "build_wall_s": wall_s,
        "build_peak_rss_kib": peak_rss_kib,
        "patched_map_calls": patched_map_calls,
        "virtual_members": virtual_members,
        "max_virtual_member_amplification": max(row["decoded_context_amplification"] for row in virtual_members),
        "locality_within_8x": all(row["locality_within_8x"] for row in virtual_members),
    }


def _fresh_worker(arm: str, source: Path, archive: Path, output: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--worker-arm", arm,
         "--source", str(source), "--archive", str(archive), "--worker-output", str(output)],
        cwd=ROOT, env=env, check=True, capture_output=True, text=True,
    )
    if not output.is_file():
        raise RuntimeError(f"R37 worker emitted no result: {completed.stdout!r} {completed.stderr!r}")
    return json.loads(output.read_text())


def _summary(reps: list[dict]) -> dict:
    identities = {(row["archive_bytes"], row["archive_sha256"]) for row in reps}
    return {
        "deterministic_within_run": len(identities) == 1,
        "archive_bytes": int(statistics.median(row["archive_bytes"] for row in reps)),
        "archive_sha256": next(iter(identities))[1] if len(identities) == 1 else "",
        "build_wall_s": float(statistics.median(row["build_wall_s"] for row in reps)),
        "build_peak_rss_kib": int(statistics.median(row["build_peak_rss_kib"] for row in reps)),
        "max_virtual_member_amplification": max(row["max_virtual_member_amplification"] for row in reps),
        "locality_within_8x": all(row["locality_within_8x"] for row in reps),
        "strong_verify_ok": all(row["strong_verify_ok"] for row in reps),
        "patched_map_calls": [int(row["patched_map_calls"]) for row in reps],
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    full, nested, identity = R34.build_sources(work_root)
    result = {
        "schema": SCHEMA,
        "status": "diagnostic-only-no-release-credit",
        "evidence_head": os.environ.get("CMPCT_EVIDENCE_HEAD", ""),
        "parent_r36_result": "R36_REGENERABLE_DEFLATE_PROJECT_WAIT_OWNER_RESULT.md",
        "identity": identity,
        "repetitions": REPETITIONS,
        "targets": {},
    }
    valid = True
    locality_failure = False
    runtime_or_rss_regression = False
    promotion_runtime = True

    for target_name, source in {"full-backups": full, "nested-only": nested}.items():
        target = {"arms": {}}
        for arm in ARMS:
            reps = []
            for rep in range(REPETITIONS):
                archive = work_root / "archives" / target_name / arm / f"{rep}.cmpct"
                output = work_root / "workers" / target_name / arm / f"{rep}.json"
                output.parent.mkdir(parents=True, exist_ok=True)
                reps.append(_fresh_worker(arm, source, archive, output))
            target["arms"][arm] = {"repetitions": reps, "median": _summary(reps)}

        release = target["arms"]["release-all-exact"]["median"]
        control = target["arms"]["candidate-map-control"]["median"]
        candidate = target["arms"]["candidate-wait-once"]["median"]
        identity_ok = (
            release["deterministic_within_run"] and control["deterministic_within_run"] and candidate["deterministic_within_run"]
            and release["strong_verify_ok"] and control["strong_verify_ok"] and candidate["strong_verify_ok"]
            and candidate["archive_bytes"] < release["archive_bytes"]
            and candidate["archive_bytes"] == control["archive_bytes"]
            and candidate["archive_sha256"] == control["archive_sha256"]
            and candidate["patched_map_calls"] == [1, 1, 1]
            and control["patched_map_calls"] == [0, 0, 0]
            and release["patched_map_calls"] == [0, 0, 0]
        )
        valid = valid and identity_ok
        locality_failure = locality_failure or not candidate["locality_within_8x"]

        improvement_s = control["build_wall_s"] - candidate["build_wall_s"]
        candidate["wall_improvement_vs_map_s"] = improvement_s
        candidate["wall_improvement_vs_map_fraction"] = improvement_s / control["build_wall_s"] if control["build_wall_s"] else None
        candidate["material_regression_vs_release"] = _material_runtime_regression(release["build_wall_s"], candidate["build_wall_s"])
        candidate["rss_delta_fraction_vs_map"] = (
            (candidate["build_peak_rss_kib"] - control["build_peak_rss_kib"]) / control["build_peak_rss_kib"]
            if control["build_peak_rss_kib"] else None
        )
        candidate["rss_over_10pct_vs_map"] = bool(
            control["build_peak_rss_kib"] and candidate["build_peak_rss_kib"] > 1.10 * control["build_peak_rss_kib"]
        )
        runtime_or_rss_regression = runtime_or_rss_regression or candidate["material_regression_vs_release"] or candidate["rss_over_10pct_vs_map"]
        promotion_runtime = promotion_runtime and improvement_s > 0 and not candidate["material_regression_vs_release"]
        if target_name == "nested-only":
            promotion_runtime = promotion_runtime and improvement_s >= 0.010
        target["identity_ok"] = identity_ok
        result["targets"][target_name] = target

    if not valid:
        decision = "SUBSTRATE_OR_IDENTITY_FAILURE"
    elif locality_failure:
        decision = "WAIT_ONCE_LOCALITY_FAILURE"
    elif runtime_or_rss_regression:
        decision = "WAIT_ONCE_RUNTIME_OR_RSS_REGRESSION"
    elif promotion_runtime:
        decision = "PROMOTE_WAIT_ONCE_SCHEDULING_BOUNDARY"
    else:
        decision = "WAIT_ONCE_INSUFFICIENT"
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
