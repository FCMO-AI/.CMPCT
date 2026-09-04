from __future__ import annotations

"""Frozen R33 phase-attribution diagnostic for R32 residual create-time debt."""

import argparse
import cProfile
import hashlib
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
from benchmarks import v030_release_ablation_canonical as A
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "cmpct-v030-r33-regenerable-deflate-residual-phase-attribution-v1"
REPETITIONS = 3
ARMS = ("release-all-exact", "no-ordinary-zstd")
EXPECTED = {
    "full-backups": {
        "release-all-exact": (8088619, "dc789b874da673584046af26e7f21f593cfcc1fa8cd365bc6298942c2f752eb7"),
        "no-ordinary-zstd": (8056193, "d812ffa7a0002e4e137e578918010d5ce00dfb8055a4c9fb188ebbd9212c79e9"),
    },
    "nested-only": {
        "release-all-exact": (2231160, "6d6973cb4931edcc2ed776b8fdb8500dc80da084f0b06681e87eff544646d6ef"),
        "no-ordinary-zstd": (2197414, "b2cb86d7c51eecec959989b3e592f344311c3da32af3d47ed1251284f2223bea"),
    },
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def interesting(filename: str) -> bool:
    s = filename.replace("\\", "/")
    return "/src/cmpct/" in s or s.endswith("v030_r32_regenerable_deflate_output_dead_zstd_elision.py") or "entropygraph_v030_release_product" in s


def profile_build_worker(arm: str, source: Path, archive: Path) -> dict:
    profiler = cProfile.Profile()
    started = time.perf_counter()
    result = profiler.runcall(R32._build_arm, arm, source, archive)
    wall = time.perf_counter() - started
    stats = pstats.Stats(profiler)
    rows = []
    for (filename, line, name), (cc, nc, tt, ct, _callers) in stats.stats.items():
        if not interesting(filename):
            continue
        rows.append({
            "signature": f"{Path(filename).name}:{line}:{name}",
            "calls": int(nc),
            "primitive_calls": int(cc),
            "internal_s": float(tt),
            "cumulative_s": float(ct),
        })
    rows.sort(key=lambda r: (-r["cumulative_s"], r["signature"]))
    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok"):
        raise RuntimeError(f"{arm} strong verification failed: {verified!r}")
    if verified.get("tree_sha256") != PRODUCT.treehash(source):
        raise RuntimeError(f"{arm} product tree mismatch")
    return {
        "wall_s": wall,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": sha256_file(archive),
        "strong_verify_ok": True,
        "profile": rows,
        "top40": rows[:40],
        "build_stats": result[0],
    }


def profile_build_fresh(arm: str, source: Path, archive: Path, worker_output: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    worker_output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-arm", arm,
            "--source", str(source),
            "--archive", str(archive),
            "--worker-output", str(worker_output),
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    if not worker_output.is_file():
        raise RuntimeError(f"R33 worker {arm} emitted no result: {completed.stdout!r} {completed.stderr!r}")
    return json.loads(worker_output.read_text())


def build_sources(work_root: Path) -> tuple[Path, Path, dict]:
    full = None
    expected_tree = observed_tree = None
    for suite, source, expected in A._build_corpora(work_root / "corpus"):
        if suite == R32.TARGET_SUITE and source.name == R32.TARGET_NAME:
            full = source
            expected_tree = str(expected["tree_sha256"])
            observed_tree = A.RC.treehash(source)
            break
    if full is None or expected_tree is None or observed_tree != expected_tree:
        raise RuntimeError("R33 frozen corpus identity failure")
    nested_file = full / R32.NESTED_MEMBER
    nested_sha = sha256_file(nested_file)
    nested = work_root / "nested-only"
    nested.mkdir(parents=True)
    shutil.copyfile(nested_file, nested / R32.NESTED_MEMBER)
    return full, nested, {"tree_sha256": observed_tree, "nested_sha256": nested_sha}


def median_profiles(reps: list[dict]) -> dict[str, dict]:
    signatures = sorted({row["signature"] for rep in reps for row in rep["profile"]})
    out = {}
    for sig in signatures:
        vals = []
        for rep in reps:
            row = next((x for x in rep["profile"] if x["signature"] == sig), None)
            vals.append(row or {"calls": 0, "internal_s": 0.0, "cumulative_s": 0.0})
        out[sig] = {
            "calls": int(statistics.median(x["calls"] for x in vals)),
            "internal_s": float(statistics.median(x["internal_s"] for x in vals)),
            "cumulative_s": float(statistics.median(x["cumulative_s"] for x in vals)),
        }
    return out


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    full, nested, identity = build_sources(work_root)
    targets = {"full-backups": full, "nested-only": nested}
    result = {
        "schema": SCHEMA,
        "status": "diagnostic-only-no-release-credit",
        "evidence_head": os.environ.get("CMPCT_EVIDENCE_HEAD", ""),
        "parent_r32_head": "0b1f3cd653f0e2489964b93cdd19fa8324adda2e",
        "identity": identity,
        "repetitions": REPETITIONS,
        "targets": {},
    }
    identity_ok = True
    for target_name, source in targets.items():
        target = {"arms": {}}
        for arm in ARMS:
            reps = []
            for rep in range(REPETITIONS):
                archive = work_root / "archives" / target_name / arm / f"{rep}.cmpct"
                archive.parent.mkdir(parents=True, exist_ok=True)
                worker_output = work_root / "workers" / target_name / arm / f"{rep}.json"
                row = profile_build_fresh(arm, source, archive, worker_output)
                exp_bytes, exp_sha = EXPECTED[target_name][arm]
                row["identity_ok"] = row["archive_bytes"] == exp_bytes and row["archive_sha256"] == exp_sha
                identity_ok = identity_ok and row["identity_ok"]
                reps.append(row)
            target["arms"][arm] = {
                "repetitions": reps,
                "median_wall_s": float(statistics.median(r["wall_s"] for r in reps)),
                "median_profile": median_profiles(reps),
            }
        release = target["arms"]["release-all-exact"]["median_profile"]
        candidate = target["arms"]["no-ordinary-zstd"]["median_profile"]
        sigs = sorted(set(release) | set(candidate))
        deltas = []
        for sig in sigs:
            r = release.get(sig, {"cumulative_s": 0.0, "internal_s": 0.0, "calls": 0})
            c = candidate.get(sig, {"cumulative_s": 0.0, "internal_s": 0.0, "calls": 0})
            deltas.append({
                "signature": sig,
                "cumulative_delta_s": c["cumulative_s"] - r["cumulative_s"],
                "internal_delta_s": c["internal_s"] - r["internal_s"],
                "call_delta": c["calls"] - r["calls"],
            })
        deltas.sort(key=lambda x: (-x["cumulative_delta_s"], x["signature"]))
        target["positive_cumulative_deltas"] = [d for d in deltas if d["cumulative_delta_s"] > 0][:40]
        result["targets"][target_name] = target

    if not identity_ok:
        result["decision"] = "SUBSTRATE_OR_IDENTITY_FAILURE"
        return result

    full_delta = {d["signature"]: d for d in result["targets"]["full-backups"]["positive_cumulative_deltas"]}
    nested_delta = {d["signature"]: d for d in result["targets"]["nested-only"]["positive_cumulative_deltas"]}
    localized = []
    for sig, n in nested_delta.items():
        f = full_delta.get(sig)
        if f and n["cumulative_delta_s"] >= 0.010 and f["cumulative_delta_s"] > 0:
            localized.append({"signature": sig, "nested_delta_s": n["cumulative_delta_s"], "full_delta_s": f["cumulative_delta_s"]})
    localized.sort(key=lambda x: (-x["nested_delta_s"], x["signature"]))
    result["localized_owners"] = localized
    result["decision"] = "PHASE_OWNER_LOCALIZED" if localized else "RESIDUAL_DISTRIBUTED_OR_BELOW_ATTRIBUTION_FLOOR"
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
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        row = profile_build_worker(args.worker_arm, args.source, args.archive)
        args.worker_output.parent.mkdir(parents=True, exist_ok=True)
        args.worker_output.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"worker_arm": args.worker_arm, "output": str(args.worker_output)}))
        return
    if args.work_root is None or args.output is None:
        ap.error("parent mode requires --work-root and --output")
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
