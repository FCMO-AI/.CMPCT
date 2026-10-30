#!/usr/bin/env python3
"""J24G61: independent phase-attribution on J24G60's physical signed one-op archives.

Research instrumentation only. Exact source, same-state oracle, no CMPCT product edits.
"""
from __future__ import annotations

import cProfile
import hashlib
import json
import os
from pathlib import Path
import platform
import pstats
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

import j24g60_single_delta_chain_court as parent
import cmpct.reader as reader

PREREG = "8eaa7460825fde317aa7338db3f557a2dd9e45bf"
PARENT = "fb5d96cdb8855fe3e01868792e65b79d3d61661d"
CASES = ((512, 63), (2048, 1), (2048, 32), (2048, 63))


def probe(path: Path, instrument: bool) -> dict:
    """The two wrapped spans do not nest; difference is residual Reader work."""
    replay = {"ns": 0, "calls": 0}
    footer = {"ns": 0, "calls": 0}
    original_replay = reader._apply_journal_ops
    original_footer = reader.CMPCT._decode_generation_payload

    def traced_replay(*args, **kwargs):
        start = time.perf_counter_ns()
        try:
            return original_replay(*args, **kwargs)
        finally:
            replay["ns"] += time.perf_counter_ns() - start
            replay["calls"] += 1

    def traced_footer(self, *args, **kwargs):
        start = time.perf_counter_ns()
        try:
            return original_footer(self, *args, **kwargs)
        finally:
            footer["ns"] += time.perf_counter_ns() - start
            footer["calls"] += 1

    if instrument:
        reader._apply_journal_ops = traced_replay
        reader.CMPCT._decode_generation_payload = traced_footer
    try:
        c0 = time.process_time_ns()
        w0 = time.perf_counter_ns()
        ar = reader.CMPCT(path)
        wall = time.perf_counter_ns() - w0
        cpu = time.process_time_ns() - c0
        try:
            rows = len(ar.files)
            depth = ar.delta_depth
            last_footer = ar.latest_footer_pos
        finally:
            ar.close()
    finally:
        reader._apply_journal_ops = original_replay
        reader.CMPCT._decode_generation_payload = original_footer
    assert not instrument or replay["ns"] + footer["ns"] <= wall
    return {
        "instrumented": instrument, "wall_ns": wall, "cpu_ns": cpu,
        "replay_wall_ns": replay["ns"], "replay_calls": replay["calls"],
        "footer_wall_ns": footer["ns"], "footer_calls": footer["calls"],
        "residual_wall_ns": wall - replay["ns"] - footer["ns"],
        "rows": rows, "depth": depth, "last_footer": last_footer,
        "vmhwm_kib": parent.vmhwm_kib(),
    }


def profile_one(path: Path) -> dict:
    """Second observer; cProfile alters time and is never mixed with paired wall."""
    profiler = cProfile.Profile()
    profiler.enable()
    with reader.CMPCT(path) as ar:
        rows = len(ar.files)
        depth = ar.delta_depth
    profiler.disable()
    stats = pstats.Stats(profiler)
    items = []
    for (filename, line, name), (primitive, total, own, cum, callers) in stats.stats.items():
        if any(filename.endswith(s) for s in ("journal_replay.py", "reader.py")):
            items.append({
                "file": Path(filename).name, "line": line, "function": name,
                "primitive_calls": primitive, "total_calls": total,
                "self_s": own, "cumulative_s": cum,
            })
    items.sort(key=lambda item: item["cumulative_s"], reverse=True)
    return {"rows": rows, "depth": depth, "total_profile_calls": stats.total_calls,
            "top_functions": items[:35]}


def child(script: Path, path: Path, instrument: bool, env: dict) -> dict:
    args = [sys.executable, "-B", str(script), "--probe", str(path),
            "1" if instrument else "0"]
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, env=env, timeout=90, check=False)
    assert proc.returncode == 0, (proc.returncode, proc.stderr[-2000:])
    return json.loads(proc.stdout)


def median(rows: list[dict], field: str) -> float:
    return float(statistics.median(row[field] for row in rows))


def summarize(rows: list[dict], n: int, depth: int) -> dict:
    pair = [r for r in rows if r["n"] == n and r["depth"] == depth
            and r["instrumented"]]
    a = [r for r in pair if r["variant"] == "chain"]
    b = [r for r in pair if r["variant"] == "checkpoint"]
    assert len(a) == len(b) == 8
    out = {
        "chain_open_wall_ns": median(a, "wall_ns"),
        "checkpoint_open_wall_ns": median(b, "wall_ns"),
        "chain_open_cpu_ns": median(a, "cpu_ns"),
        "checkpoint_open_cpu_ns": median(b, "cpu_ns"),
        "chain_replay_ns": median(a, "replay_wall_ns"),
        "checkpoint_replay_ns": median(b, "replay_wall_ns"),
        "chain_footer_ns": median(a, "footer_wall_ns"),
        "checkpoint_footer_ns": median(b, "footer_wall_ns"),
        "chain_residual_ns": median(a, "residual_wall_ns"),
        "checkpoint_residual_ns": median(b, "residual_wall_ns"),
    }
    difference = out["chain_open_wall_ns"] - out["checkpoint_open_wall_ns"]
    replay = out["chain_replay_ns"] - out["checkpoint_replay_ns"]
    out["extra_total_wall_ns"] = difference
    out["extra_replay_wall_ns"] = replay
    out["extra_replay_fraction"] = replay / difference if difference > 0 else None
    return out


def run() -> None:
    identity = parent.verify_source()
    root = Path(__file__).resolve().parents[1]
    assert subprocess.run(["git", "merge-base", "--is-ancestor", PARENT, "HEAD"],
                          cwd=root).returncode == 0
    assert subprocess.run(["git", "merge-base", "--is-ancestor", PREREG, "HEAD"],
                          cwd=root).returncode == 0
    records: list[dict] = []
    report = {
        "status": "RESEARCH_ONLY", "decision": "INCONCLUSIVE",
        "source": identity, "parent_research_head": PARENT,
        "prereg_commit": PREREG, "platform": platform.platform(),
        "python": platform.python_version(), "cases": {}, "raw_samples": records,
        "profile": {}, "limits": [
            "same-state checkpoint is private research oracle, not public Writer output",
            "instrumented and uninstrumented absolute wall times are separate strata",
            "cProfile changes CPU time and its samples are diagnostic only",
            "fresh-process open excludes Python startup/import and does not imply cold disk",
            "zero native xattrs in synthetic generator; metadata-heavy generalization unmeasured",
            "no full product create/extract/RSS/recovery or ZIP/Zstd comparator credit",
        ],
    }
    env = dict(os.environ)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g61-") as tmp:
        stage = Path(tmp)
        pycache = stage / "pycache"
        pycache.mkdir()
        env["PYTHONPYCACHEPREFIX"] = str(pycache)
        for n in (512, 2048):
            corpus = stage / f"source-{n}"
            corpus.mkdir()
            for i in range(n):
                (corpus / f"f{i:04d}.dat").write_bytes(
                    hashlib.sha256(f"generic-record-{i}".encode()).digest() * 2
                )
            snapshots = parent.make_case(corpus, stage, n)
            for size, depth in CASES:
                if size != n:
                    continue
                entry = snapshots[str(depth)]
                paths = {kind: Path(entry["paths"][kind])
                         for kind in ("chain", "checkpoint")}
                assert len(entry["public_chain_wire"]) == depth + 1
                assert all(x["op_width"] == 1 for x in
                           entry["public_chain_wire"][:-1])
                report["cases"][f"{n}/{depth}"] = {
                    "archive_bytes": entry["archive_bytes"],
                    "archive_sha256": entry["archive_sha256"],
                    "checkpoint_premium_bytes": entry["checkpoint_premium_bytes"],
                    "physical_depth": depth,
                    "index_count": entry["semantics"]["index_count"],
                }
                for block in range(4):
                    seq = ("chain", "checkpoint", "checkpoint", "chain") if block % 2 == 0 else (
                        "checkpoint", "chain", "chain", "checkpoint")
                    for position, variant in enumerate(seq):
                        obs = child(Path(__file__).resolve(), paths[variant], True, env)
                        assert obs["rows"] == n and obs["depth"] == (
                            depth if variant == "chain" else 0)
                        assert obs["replay_calls"] == (
                            depth if variant == "chain" else 0)
                        assert obs["footer_calls"] == (
                            depth + 1 if variant == "chain" else 1)
                        records.append({"n": n, "depth": depth, "variant": variant,
                                        "block": block, "position": position, **obs})
                if n == 2048 and depth == 63:
                    # Separate, alternating uninstrumented reference stratum.
                    for block in range(2):
                        seq = ("chain", "checkpoint", "checkpoint", "chain") if block == 0 else (
                            "checkpoint", "chain", "chain", "checkpoint")
                        for position, variant in enumerate(seq):
                            obs = child(Path(__file__).resolve(), paths[variant], False, env)
                            assert obs["rows"] == n
                            records.append({"n": n, "depth": depth, "variant": variant,
                                            "block": block, "position": position, **obs})
                    report["profile"]["chain"] = profile_one(paths["chain"])
                    report["profile"]["checkpoint"] = profile_one(paths["checkpoint"])
        summaries = {}
        for n, d in CASES:
            summaries[f"{n}/{d}"] = summarize(records, n, d)
        report["summaries"] = summaries
        primary = summaries["2048/63"]
        raw = [r for r in records if r["n"] == 2048 and r["depth"] == 63
               and not r["instrumented"]]
        a = [r for r in raw if r["variant"] == "chain"]
        b = [r for r in raw if r["variant"] == "checkpoint"]
        assert len(a) == len(b) == 4
        raw_difference = median(a, "wall_ns") - median(b, "wall_ns")
        instrumented_difference = primary["extra_total_wall_ns"]
        impact = abs(raw_difference - instrumented_difference) / raw_difference if raw_difference > 0 else None
        report["control"] = {
            "uninstrumented_chain_ns": median(a, "wall_ns"),
            "uninstrumented_checkpoint_ns": median(b, "wall_ns"),
            "uninstrumented_difference_ns": raw_difference,
            "instrumented_difference_ns": instrumented_difference,
            "penalty_perturbation_fraction": impact,
        }
        share = primary["extra_replay_fraction"]
        if impact is None or impact > .15 or instrumented_difference < 3_000_000:
            verdict = "INCONCLUSIVE_MEASUREMENT_OR_NONMATERIAL_PENALTY"
        elif share is not None and share >= .50:
            verdict = "REPLAY_MAJOR_COST_OWNER_ON_MEASURED_WORKLOAD"
        elif share is not None and share < .35:
            verdict = "REPLAY_NOT_MAJOR_COST_OWNER_ON_MEASURED_WORKLOAD"
        else:
            verdict = "INCONCLUSIVE_REPLAY_SHARE"
        report["decision"] = verdict
    dest = Path(os.environ.get("J24G61_RESULT", "evidence/j24g61-result.json"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("J24G61_RESULT", verdict)
    print("J24G61_PRIMARY", json.dumps(primary, sort_keys=True))
    print("J24G61_CONTROL", json.dumps(report["control"], sort_keys=True))
    print("J24G61_RECEIPT", parent.sha256_file(dest))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--probe":
        print(json.dumps(probe(Path(sys.argv[2]), sys.argv[3] == "1"), sort_keys=True))
    else:
        run()
