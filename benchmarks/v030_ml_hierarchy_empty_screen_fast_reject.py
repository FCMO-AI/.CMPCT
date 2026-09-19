from __future__ import annotations

"""Fresh-process ML create oracle for skipping impossible hierarchical auditions.

The canonical G0-G4 owner first computes the flat G1/G2 incumbent and then calls
Hierarchical Geometry.  On the exact-parent ML artifact all 19 records reported zero
hierarchical screened candidates, yet HG.audition still recompresses every raw record at
level 19 before discovering that fact.  This oracle performs only the content-derived
primary/secondary nomination first; when no pair exists it returns the already-computed
flat incumbent byte-for-byte.  Candidate-bearing records use the untouched owner.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
ORDERS = (("control", "fast"), ("fast", "control"))


def install_fast_reject() -> dict[str, int]:
    # This is the actual canonical object reached by release_product -> release_product_base.C.
    G = PRODUCT._BASE_IMPL.C.SHARED.G
    original = G._audition_record
    counts = {"fast_rejects": 0, "fallback_original": 0}

    def audition(record_id, record, member_lengths):
        G._assert_codec_identity()
        raw = G.A5._decode_record(record)
        flat_record, flat_descriptor, flat_stats = G.O._audition_record(record_id, record, member_lengths)
        stats = dict(flat_stats)
        stats["hierarchical_screened_candidates"] = 0
        stats["hierarchical_exact_finalists"] = 0
        stats["hierarchical_incremental_saving_bytes"] = 0
        amp = float(stats.get("max_member_read_amplification", float("inf")))
        if not (G.O.MIN_RECORD_BYTES <= len(raw) <= G.MAX_OVERLAY_RECORD) or amp > G.MAX_MEMBER_READ_AMP:
            counts["fast_rejects"] += 1
            return flat_record, flat_descriptor, stats

        # HG cannot produce a screened candidate unless at least one primary/secondary
        # pair exists.  Prove that cheaper necessary condition before HG pays its direct
        # level-19 recompression.  No workload/file identity participates.
        possible = False
        for primary in G.HG.primary_candidates(raw):
            rows = raw.split(bytes((primary,)))
            if G.HG.secondary_candidates(rows, primary):
                possible = True
                break
        if not possible:
            counts["fast_rejects"] += 1
            return flat_record, flat_descriptor, stats
        counts["fallback_original"] += 1
        return original(record_id, record, member_lengths)

    G._audition_record = audition
    return counts


def worker(arm: str, source: Path, archive: Path) -> dict:
    counts = {"fast_rejects": 0, "fallback_original": 0}
    if arm == "fast":
        counts = install_fast_reject()
    started_cpu = time.process_time()
    started = time.perf_counter()
    stats = PRODUCT.build(source, archive)
    wall = time.perf_counter() - started
    cpu = time.process_time() - started_cpu
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok"):
        raise RuntimeError(f"product verify failed: {verified}")
    return {
        "arm": arm,
        "wall_s": wall,
        "cpu_s": cpu,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "tree_sha256": verified.get("tree_sha256"),
        "selected": stats.get("selected"),
        **counts,
    }


def fresh(arm: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cp = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--worker", arm, "--source", str(source), "--archive", str(archive)],
        cwd=ROOT, env=env, check=True, capture_output=True, text=True,
    )
    return json.loads([line for line in cp.stdout.splitlines() if line.strip()][-1])


def run(root: Path) -> dict:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    source = PERF._build_corpora(root / "corpora")[("neutral_hostile_v1", "09_ml_artifacts")]
    pairs = []
    for rep, order in enumerate(ORDERS):
        rows = {arm: fresh(arm, source, root / f"r{rep}-{arm}.cmpct") for arm in order}
        c, f = rows["control"], rows["fast"]
        if c["archive_sha256"] != f["archive_sha256"] or c["tree_sha256"] != f["tree_sha256"]:
            raise RuntimeError("archive/tree identity drift")
        if f["fast_rejects"] < 1:
            raise RuntimeError("fast arm rejected no impossible hierarchical auditions")
        pairs.append({
            "rep": rep, "order": list(order), "rows": rows,
            "wall_improvement_pct": (c["wall_s"] - f["wall_s"]) / c["wall_s"] * 100.0,
            "cpu_improvement_pct": (c["cpu_s"] - f["cpu_s"]) / c["cpu_s"] * 100.0,
        })
    wall = sorted(float(p["wall_improvement_pct"]) for p in pairs)
    median = sum(wall) / len(wall)
    return {
        "schema": "cmpct-v030-ml-hierarchy-empty-screen-fast-reject-v1",
        "release_credit": False,
        "source_sha": os.environ.get("EVIDENCE_HEAD"),
        "pairs": pairs,
        "median_wall_improvement_pct": median,
        "exact_parent_ml_create_ratio": 1.4042356480057694,
        "required_relative_improvement_for_1_25": 10.983601521924591,
        "decision": "advance" if median > 10.983601521924591 else "kill-or-narrow",
        "claim_boundary": "research scheduler/audition oracle; exact archive bytes required; no release credit",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", choices=("control", "fast"))
    ap.add_argument("--source", type=Path)
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--root", type=Path, default=Path("benchmark-artifacts/v030-ml-hierarchy-empty-screen"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-ml-hierarchy-empty-screen.json"))
    args = ap.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker, args.source, args.archive), separators=(",", ":")))
        return
    result = run(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
