#!/usr/bin/env python3
"""J24I55: phase ownership, not another READ-prefix timing hypothesis."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile

from j24i54_builder_prefix_read_court import sha_file, tree_fingerprint, git

PARENT = "444401e36fcd27558c13702ad01c01cfa206cf7f"
PREREG = "9db7839bcad97748deb1110ca3944280e95ff1f8"
STAGES = ("scan", "_build_micro_packs", "_prepare_deflate_reuse",
          "_train_dictionary", "ordered_encode", "residual")

def median(values):
    values = list(values)
    assert values
    return statistics.median(values)

def contrast(rows, a, b, metric):
    def get(row):
        if metric in ("wall_ms", "cpu_ms"):
            return row["total"][metric]
        if metric in ("minor_faults", "major_faults"):
            return row[metric]
        stage, field = metric.split("/")
        return row["residual"][field] if stage == "residual" else row["phases"][stage][field]
    x = median(get(s) for r in rows if r["mode"] == a for s in r["samples"])
    y = median(get(s) for r in rows if r["mode"] == b for s in r["samples"])
    return {"base": x, "treatment": y, "delta": y-x, "ratio": y/x if x else None}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--reps", type=int, default=3)
    args = ap.parse_args()
    assert 1 <= args.reps <= 7
    root = Path(__file__).resolve().parents[1]
    head = git("rev-parse", "HEAD")
    assert head == os.environ.get("EVIDENCE_HEAD"), ("not exact HEAD", head)
    for ancestor in (PARENT, PREREG):
        subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, head], check=True)
    sys.path.insert(0, str(root/"benchmarks"))
    import universal_bench as u
    scratch = Path(tempfile.mkdtemp(prefix="cmpct-j24i55-"))
    try:
        u.WORK = scratch
        u.CORP = scratch/"corpora"
        u.OUT = scratch/"outputs"
        u.CORP.mkdir()
        u.OUT.mkdir()
        u.make_corpora()
        fingerprint = tree_fingerprint(u.CORP)
        sources = ["src/cmpct/builder.py", "src/cmpct/native_codec.py",
                   "src/cmpct/_ordered_pull.py", "research/j24i55_phase_child.py",
                   "research/j24i55_builder_phase_court.py"]
        source_sha = {p: sha_file(root/p) for p in sources}
        groups = [("EXPERIMENT", ["FRESH", "BUILD", "BUILD", "FRESH"]),
                  ("EXPERIMENT", ["BUILD", "FRESH", "FRESH", "BUILD"]),
                  ("SHAM", ["FRESH", "FRESH", "FRESH", "FRESH"])]
        observations = []
        args.out.parent.mkdir(parents=True, exist_ok=True)
        preserved_archive = args.out.parent/"j24i55-binary.cmpct"
        preserved_native = args.out.parent/"j24i55-native.so"
        for g, (court, order) in enumerate(groups):
            for slot, mode in enumerate(order):
                out = scratch/"outputs"/f"binary-{g}-{slot}.cmpct"
                env = dict(os.environ, PYTHONPATH=str(root/"src"))
                cmd = [sys.executable, str(root/"research"/"j24i55_phase_child.py"),
                       str(root), str(u.CORP), str(out), mode, str(args.reps)]
                run = subprocess.run(cmd, env=env, text=True, capture_output=True)
                if run.returncode:
                    print("CHILD_STDERR", run.stderr, file=sys.stderr)
                    print("CHILD_STDOUT", run.stdout, file=sys.stderr)
                    raise RuntimeError(f"child failed group {g} slot {slot} mode {mode}")
                row = json.loads(run.stdout)
                assert row["mode"] == mode and len(row["samples"]) == args.reps
                row.update({"group": g, "slot": slot, "court": court,
                            "label": "A" if slot % 2 == 0 else "B"})
                observations.append(row)
                if not preserved_archive.exists():
                    shutil.copy2(out, preserved_archive)
                    shutil.copy2(Path(row["native_path"]), preserved_native)
                out.unlink()
                print("COURT", g, slot, mode,
                      "wall", median(s["total"]["wall_ms"] for s in row["samples"]),
                      "cpu", median(s["total"]["cpu_ms"] for s in row["samples"]),
                      flush=True)
        archive_shas = {s["archive_sha256"] for r in observations for s in r["samples"]}
        archive_sizes = {s["archive_bytes"] for r in observations for s in r["samples"]}
        native_shas = {r["native_sha256"] for r in observations}
        origins = {r["package"] for r in observations}
        assert len(archive_shas) == len(archive_sizes) == len(native_shas) == len(origins) == 1
        assert sha_file(preserved_archive) == next(iter(archive_shas))
        assert sha_file(preserved_native) == next(iter(native_shas))
        assert tree_fingerprint(u.CORP) == fingerprint, "source mutated"
        for r in observations:
            for s in r["samples"]:
                assert set(s["phases"]) == set(STAGES)-{"residual"}
                for field in ("wall_ms", "cpu_ms"):
                    assert abs(s["total"][field] -
                           (sum(v[field] for v in s["phases"].values())+s["residual"][field])) < 1e-6
                assert s["minor_faults"] >= 0 and s["major_faults"] >= 0
        experiment = [r for r in observations if r["court"] == "EXPERIMENT"]
        sham = [r for r in observations if r["court"] == "SHAM"]
        def suite(rows):
            keys = ["wall_ms", "cpu_ms", "minor_faults", "major_faults"]
            keys += [s+"/"+k for s in STAGES for k in ("wall_ms", "cpu_ms")]
            return {key: contrast(rows, "FRESH", "BUILD", key) for key in keys}
        aggregate = suite(experiment)
        by_group = {str(g): suite([r for r in experiment if r["group"] == g]) for g in (0, 1)}
        sham_a = [{**r, "mode": r["label"]} for r in sham]
        sham_metrics = {key: contrast(sham_a, "A", "B", key) for key in ("wall_ms", "cpu_ms")}
        delta_cpu = aggregate["cpu_ms"]["delta"]
        delta_wall = aggregate["wall_ms"]["delta"]
        encode_cpu = aggregate["ordered_encode/cpu_ms"]["delta"]
        share = encode_cpu/delta_cpu if delta_cpu > 0 else None
        stable = all(by_group[str(g)][key]["delta"] > 3.0
                     for g in (0, 1) for key in ("wall_ms", "cpu_ms"))
        clean_sham = all(abs(s["delta"]) <= 3 and (s["ratio"] is None or
                         abs(s["ratio"]-1) <= .05) for s in sham_metrics.values())
        if not (stable and clean_sham and delta_cpu > 3 and delta_wall > 3):
            decision = "NOT_STABLE_OR_SHAM_AMBIGUOUS"
        elif share is not None and share >= .60 and encode_cpu >= 3 and all(
                by_group[str(g)]["ordered_encode/cpu_ms"]["delta"] > 0 for g in (0,1)):
            decision = "ENCODE_STAGE_OWNER_SUPPORTED"
        elif share is not None and share <= .30:
            decision = "NON_ENCODE_STAGE_BURDEN_SUPPORTED"
        else:
            decision = "DISTRIBUTED_OR_AMBIGUOUS"
        result = {
            "schema": "cmpct-j24i55-builder-phase-v1",
            "evidence_head": head, "prereg_commit": PREREG, "base_exact": PARENT,
            "platform": platform.platform(), "python": sys.version,
            "input_tree": fingerprint, "source_sha256": source_sha,
            "physical_archive": {"file": preserved_archive.name,
                                 "size": next(iter(archive_sizes)),
                                 "sha256": next(iter(archive_shas))},
            "physical_native": {"file": preserved_native.name, "sha256": next(iter(native_shas))},
            "observations": observations, "reps": args.reps,
            "aggregate": aggregate, "groups": by_group, "sham": sham_metrics,
            "encode_cpu_share_of_total_delta": share, "decision": decision,
            "scope": "source-identical instrumented Builder research only; not a product timing or release result",
            "utc": datetime.now(timezone.utc).isoformat()
        }
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
        print("J24I55_RESULT", json.dumps({"decision": decision,
              "total_wall": aggregate["wall_ms"], "total_cpu": aggregate["cpu_ms"],
              "encode_cpu": aggregate["ordered_encode/cpu_ms"],
              "encode_cpu_share": share, "sham": sham_metrics}, sort_keys=True), flush=True)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

if __name__ == "__main__":
    main()
