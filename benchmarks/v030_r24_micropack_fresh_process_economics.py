from __future__ import annotations

"""Fresh-process economics referee for the locality-derived micro-pack mechanism.

Mission lock
============
The corrected shared-scan experiments show a strict stored-byte win wherever the
8x-derived micro-pack law emits groups, and exact no-op fallback elsewhere.  The
next falsifiable question is whether that density is bought with creation compute
or memory debt.

Hypothesis
----------
On the three current-fingerprint workloads where the mechanism actually emits
micro-packs (Developer, Incremental Backups, Tiny Files), the complete research
pipeline (r24 build + membership-v1 transform + strong verification) will remain
strictly smaller and will not regress median fresh-process CPU or wall time versus
the shared-scan no-micro-pack control.  Hosted-process RSS is measured and exposed
but is diagnostic rather than a promotion gate because import/runtime state is a
large shared component.

Disproof
--------
Any workload that loses bytes, tree exactness, <=8x locality, or median creation
CPU/wall falsifies full domination and is reported as resource/economic debt.  No
threshold sweep is permitted.

Research-only.  No canonical builder policy or release version is changed.
"""

import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time

_PROCESS_CPU_T0 = time.process_time()
_PROCESS_WALL_T0 = time.perf_counter()

from benchmarks import v030_r24_micropack_current15_transfer as CURRENT15
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from benchmarks import v030_r25_membership_complete_artifact_referee as MEMBERSHIP
from cmpct import builder as BUILDER
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET_SUFFIXES = (
    "01_developer_repository",
    "06_incremental_backups",
    "08_many_tiny_files",
)
ROUNDS = 3


def _rss_kib() -> int:
    v = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Linux reports KiB; macOS reports bytes. Hosted authority is Linux, but keep
    # the local referee portable and explicit.
    return v // 1024 if sys.platform == "darwin" else v


def _source_seal() -> dict:
    repo = Path(__file__).resolve().parents[1]
    src = Path(inspect.getsourcefile(BUILDER) or BUILDER.__file__).resolve()
    try:
        src.relative_to(repo)
    except ValueError as exc:
        raise RuntimeError(f"cmpct builder escaped exact checkout: {src}") from exc
    return {
        "repo_root": str(repo),
        "builder_source": str(src),
        "builder_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
    }


def _worker(source: Path, out_root: Path, mode: str) -> dict:
    seal = _source_seal()
    shutil.rmtree(out_root, ignore_errors=True)
    out_root.mkdir(parents=True, exist_ok=True)
    release_max = int(PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)

    if mode == "independent":
        cls = SAME.NoMicroPackBuilder
    elif mode == "derived":
        cls = BASE.LocalityDerivedBuilder
    else:
        raise ValueError(mode)

    archive = out_root / f"{mode}.r24.cmpct"
    builder = cls(source, deflate_reuse_min=0, workers=1)
    builder.micro_pack_max_file = release_max

    build_cpu0 = time.process_time(); build_wall0 = time.perf_counter()
    build_stats = dict(builder.build(archive))
    build_cpu = time.process_time() - build_cpu0
    build_wall = time.perf_counter() - build_wall0

    r24_index, r24_data = BASE._parse_r24(archive)
    locality = BASE._pack_locality(r24_index)
    verify_cpu0 = time.process_time(); verify_wall0 = time.perf_counter()
    r24_verify = PRODUCT.strong_verify(archive)
    r24_verify_cpu = time.process_time() - verify_cpu0
    r24_verify_wall = time.perf_counter() - verify_wall0
    if not r24_verify.get("ok"):
        raise RuntimeError(f"{mode} r24 strong verify failed")

    candidate = out_root / f"{mode}.membership.cmpct"
    transform_cpu0 = time.process_time(); transform_wall0 = time.perf_counter()
    transform = MEMBERSHIP._write_candidate(archive, candidate)
    transform_cpu = time.process_time() - transform_cpu0
    transform_wall = time.perf_counter() - transform_wall0

    candidate_verify_dir = out_root / "candidate-verify"
    candidate_verify_dir.mkdir(parents=True, exist_ok=True)
    cverify_cpu0 = time.process_time(); cverify_wall0 = time.perf_counter()
    cverify = MEMBERSHIP._verify_candidate(
        candidate, r24_index, str(r24_verify["tree_sha256"]), candidate_verify_dir
    )
    cverify_cpu = time.process_time() - cverify_cpu0
    cverify_wall = time.perf_counter() - cverify_wall0
    if not cverify.get("strong_tree_exact"):
        raise RuntimeError(f"{mode} membership strong verify failed")

    parsed = MEMBERSHIP._parse_candidate_bytes(candidate.read_bytes())
    if parsed["index"] != r24_index or parsed["data"] != r24_data:
        raise RuntimeError(f"{mode} membership semantic/payload drift")

    groups = list(getattr(builder, "_locality_derived_groups", []))
    return {
        "mode": mode,
        "source_seal": seal,
        "r24_bytes": archive.stat().st_size,
        "candidate_bytes": candidate.stat().st_size,
        "logical_bytes": int(build_stats.get("logical_bytes", 0)),
        "group_count": len(groups),
        "group_members": sum(int(g.get("members", 0)) for g in groups),
        "max_member_amplification": float(locality["max_member_amplification"]),
        "weighted_member_amplification": float(locality["weighted_member_amplification"]),
        "max_decode_unit_bytes": int(locality["max_decode_unit_bytes"]),
        "locality_pass": bool(locality["locality_pass"]),
        "r24_tree_exact": bool(r24_verify.get("ok")),
        "candidate_tree_exact": bool(cverify.get("strong_tree_exact")),
        "build_cpu_s": build_cpu,
        "build_wall_s": build_wall,
        "r24_verify_cpu_s": r24_verify_cpu,
        "r24_verify_wall_s": r24_verify_wall,
        "transform_cpu_s": transform_cpu,
        "transform_wall_s": transform_wall,
        "candidate_verify_cpu_s": cverify_cpu,
        "candidate_verify_wall_s": cverify_wall,
        "pipeline_cpu_s": build_cpu + r24_verify_cpu + transform_cpu + cverify_cpu,
        "pipeline_wall_s": build_wall + r24_verify_wall + transform_wall + cverify_wall,
        "fresh_process_cpu_s": time.process_time() - _PROCESS_CPU_T0,
        "fresh_process_inner_wall_s": time.perf_counter() - _PROCESS_WALL_T0,
        "peak_rss_kib": _rss_kib(),
    }


def _run_child(script: Path, source: Path, out_root: Path, mode: str) -> dict:
    cmd = [
        sys.executable, str(script), "--worker", "--source", str(source),
        "--worker-out", str(out_root), "--mode", mode,
    ]
    started = time.perf_counter()
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    parent_wall = time.perf_counter() - started
    if proc.returncode != 0:
        raise RuntimeError(
            f"fresh child failed mode={mode} rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"fresh child emitted no JSON mode={mode}")
    row = json.loads(lines[-1])
    row["fresh_process_parent_wall_s"] = parent_wall
    return row


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(r[key]) for r in rows))


def _summarize(independent: list[dict], derived: list[dict]) -> dict:
    ib = {int(r["candidate_bytes"]) for r in independent}
    db = {int(r["candidate_bytes"]) for r in derived}
    if len(ib) != 1 or len(db) != 1:
        raise RuntimeError("stored bytes changed across fresh-process rounds")
    i_bytes = next(iter(ib)); d_bytes = next(iter(db))
    i_cpu = _median(independent, "fresh_process_cpu_s")
    d_cpu = _median(derived, "fresh_process_cpu_s")
    i_wall = _median(independent, "fresh_process_parent_wall_s")
    d_wall = _median(derived, "fresh_process_parent_wall_s")
    i_rss = _median(independent, "peak_rss_kib")
    d_rss = _median(derived, "peak_rss_kib")
    locality_ok = all(bool(r["locality_pass"]) for r in derived)
    exact = all(bool(r["candidate_tree_exact"]) and bool(r["r24_tree_exact"]) for r in independent + derived)
    return {
        "independent_candidate_bytes": i_bytes,
        "derived_candidate_bytes": d_bytes,
        "delta_bytes": d_bytes - i_bytes,
        "independent_fresh_cpu_s_median": i_cpu,
        "derived_fresh_cpu_s_median": d_cpu,
        "cpu_ratio": d_cpu / i_cpu if i_cpu else None,
        "independent_fresh_wall_s_median": i_wall,
        "derived_fresh_wall_s_median": d_wall,
        "wall_ratio": d_wall / i_wall if i_wall else None,
        "independent_peak_rss_kib_median": i_rss,
        "derived_peak_rss_kib_median": d_rss,
        "rss_delta_kib": d_rss - i_rss,
        "derived_group_count": int(derived[0]["group_count"]),
        "derived_group_members": int(derived[0]["group_members"]),
        "max_member_amplification": max(float(r["max_member_amplification"]) for r in derived),
        "max_decode_unit_bytes": max(int(r["max_decode_unit_bytes"]) for r in derived),
        "tree_exact": exact,
        "locality_pass": locality_ok,
        "density_pass": d_bytes < i_bytes,
        "cpu_nonregression": d_cpu <= i_cpu,
        "wall_nonregression": d_wall <= i_wall,
        "rounds": {"independent": independent, "derived": derived},
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)
    paths, identities = CURRENT15._build(work_root / "corpus")
    fingerprint = CURRENT15._fingerprint(identities)
    selected = {}
    for suffix in TARGET_SUFFIXES:
        matches = [(k, p) for k, p in paths.items() if k.endswith("/" + suffix)]
        if len(matches) != 1:
            raise RuntimeError(f"expected one target ending {suffix}, got {[k for k,_ in matches]}")
        selected[matches[0][0]] = matches[0][1]

    script = Path(__file__).resolve()
    rows = {}
    for key, source in selected.items():
        independent=[]; derived=[]
        order = (("independent", "derived"), ("derived", "independent"), ("independent", "derived"))
        for round_i, pair in enumerate(order):
            for mode in pair:
                row = _run_child(
                    script, source,
                    work_root / "fresh" / key.replace("/", "__") / f"r{round_i}-{mode}",
                    mode,
                )
                (independent if mode == "independent" else derived).append(row)
        rows[key] = _summarize(independent, derived)

    failures = {
        "density": [k for k,r in rows.items() if not r["density_pass"]],
        "tree": [k for k,r in rows.items() if not r["tree_exact"]],
        "locality": [k for k,r in rows.items() if not r["locality_pass"]],
        "cpu": [k for k,r in rows.items() if not r["cpu_nonregression"]],
        "wall": [k for k,r in rows.items() if not r["wall_nonregression"]],
    }
    hard_fail = failures["density"] or failures["tree"] or failures["locality"]
    perf_debt = failures["cpu"] or failures["wall"]
    if hard_fail:
        verdict = "MICROPACK_FRESH_PROCESS_INVARIANT_OR_DENSITY_FAIL"
    elif perf_debt:
        verdict = "MICROPACK_DENSITY_WIN_WITH_CREATION_DEBT"
    else:
        verdict = "MICROPACK_DENSITY_AND_CREATION_DOMINATE"

    return {
        "schema": "cmpct-v030-r24-micropack-fresh-process-economics-v1",
        "experiment_valid": True,
        "release_credit": False,
        "canonical_builder_changed": False,
        "current_corpus_fingerprint": fingerprint,
        "rounds_per_contender": ROUNDS,
        "target_workloads": list(selected),
        "rows": rows,
        "failures": failures,
        "aggregate": {
            "independent_bytes": sum(r["independent_candidate_bytes"] for r in rows.values()),
            "derived_bytes": sum(r["derived_candidate_bytes"] for r in rows.values()),
            "delta_bytes": sum(r["delta_bytes"] for r in rows.values()),
            "independent_fresh_cpu_s_sum_of_medians": sum(r["independent_fresh_cpu_s_median"] for r in rows.values()),
            "derived_fresh_cpu_s_sum_of_medians": sum(r["derived_fresh_cpu_s_median"] for r in rows.values()),
            "independent_fresh_wall_s_sum_of_medians": sum(r["independent_fresh_wall_s_median"] for r in rows.values()),
            "derived_fresh_wall_s_sum_of_medians": sum(r["derived_fresh_wall_s_median"] for r in rows.values()),
            "max_member_amplification": max(r["max_member_amplification"] for r in rows.values()),
            "max_decode_unit_bytes": max(r["max_decode_unit_bytes"] for r in rows.values()),
        },
        "verdict": verdict,
        "rss_gate": "diagnostic-only-until-runtime-import-attribution",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--source", type=Path)
    ap.add_argument("--worker-out", type=Path)
    ap.add_argument("--mode", choices=("independent", "derived"))
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-micropack-fresh-process-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-micropack-fresh-process.json"))
    args = ap.parse_args()
    if args.worker:
        if args.source is None or args.worker_out is None or args.mode is None:
            raise SystemExit("worker requires --source --worker-out --mode")
        print(json.dumps(_worker(args.source, args.worker_out, args.mode), sort_keys=True), flush=True)
        return
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": result["verdict"], "aggregate": result["aggregate"], "failures": result["failures"], "rows": {k:{x:v for x,v in r.items() if x!='rounds'} for k,r in result["rows"].items()}}, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
