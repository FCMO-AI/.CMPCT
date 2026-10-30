#!/usr/bin/env python3
"""J24G65: source-bound attribution of public DELETE one-op journal Reader-open work.

Research only. No change to CMPCT product code, Writer, format or release claims.
Uses the physical J24G63 Builder+Writer court and compares identical logical state.
"""
from __future__ import annotations

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
import time

import cmpct.reader as reader
import j24g63_public_put_delete_chain_court as parent

PARENT = "7f509d244325d4b6ea6d0e752ea365f79c33a742"
PREREG = "260951c6631910ed145aebc03b1868cb5770a46c"
CASES = ((512, 63), (2048, 1), (2048, 32), (2048, 63))
BLOCKS = 4


def sha_samples(samples: list[dict]) -> str:
    return hashlib.sha256(json.dumps(
        samples, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def probe(path: Path, traced: bool) -> dict:
    """Two non-nesting wrappers measure real Reader helpers, never replace semantics."""
    replay = {"ns": 0, "calls": 0}
    footer = {"ns": 0, "calls": 0}
    old_replay = reader._apply_journal_ops
    old_footer = reader.CMPCT._decode_generation_payload

    def traced_replay(*args, **kwargs):
        start = time.perf_counter_ns()
        try:
            return old_replay(*args, **kwargs)
        finally:
            replay["ns"] += time.perf_counter_ns() - start
            replay["calls"] += 1

    def traced_footer(self, *args, **kwargs):
        start = time.perf_counter_ns()
        try:
            return old_footer(self, *args, **kwargs)
        finally:
            footer["ns"] += time.perf_counter_ns() - start
            footer["calls"] += 1

    if traced:
        reader._apply_journal_ops = traced_replay
        reader.CMPCT._decode_generation_payload = traced_footer
    try:
        cpu0 = time.process_time_ns()
        wall0 = time.perf_counter_ns()
        ar = reader.CMPCT(path)
        wall_ns = time.perf_counter_ns() - wall0
        cpu_ns = time.process_time_ns() - cpu0
        try:
            rows, depth, pos = len(ar.files), ar.delta_depth, ar.latest_footer_pos
        finally:
            ar.close()
    finally:
        reader._apply_journal_ops = old_replay
        reader.CMPCT._decode_generation_payload = old_footer
    if traced:
        assert replay["ns"] + footer["ns"] <= wall_ns, (
            replay, footer, wall_ns)
    return {
        "instrumented": traced,
        "wall_ns": wall_ns,
        "cpu_ns": cpu_ns,
        "replay_ns": replay["ns"],
        "replay_calls": replay["calls"],
        "footer_ns": footer["ns"],
        "footer_calls": footer["calls"],
        "residual_ns": wall_ns - replay["ns"] - footer["ns"],
        "rows": rows, "depth": depth, "footer_pos": pos,
    }


def run_child(script: Path, path: Path, traced: bool, env: dict) -> dict:
    child = subprocess.run(
        [sys.executable, "-B", str(script), "--probe", str(path),
         "1" if traced else "0"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env=env, timeout=90, check=False)
    assert child.returncode == 0, (child.returncode, child.stderr[-3000:])
    result = json.loads(child.stdout)
    assert type(result["wall_ns"]) is int and result["wall_ns"] > 0
    return result


def median(rows: list[dict], field: str):
    return statistics.median(row[field] for row in rows)


def summarise(samples: list[dict], n: int, depth: int) -> dict:
    rows = [r for r in samples if r["n"] == n and r["depth_case"] == depth
            and r["instrumented"]]
    a = [r for r in rows if r["variant"] == "chain"]
    b = [r for r in rows if r["variant"] == "checkpoint"]
    assert len(a) == len(b) == 8
    out = {
        "chain_open_wall_ns": median(a, "wall_ns"),
        "checkpoint_open_wall_ns": median(b, "wall_ns"),
        "chain_open_cpu_ns": median(a, "cpu_ns"),
        "checkpoint_open_cpu_ns": median(b, "cpu_ns"),
        "chain_replay_ns": median(a, "replay_ns"),
        "checkpoint_replay_ns": median(b, "replay_ns"),
        "chain_footer_ns": median(a, "footer_ns"),
        "checkpoint_footer_ns": median(b, "footer_ns"),
        "chain_residual_ns": median(a, "residual_ns"),
        "checkpoint_residual_ns": median(b, "residual_ns"),
    }
    out["extra_open_wall_ns"] = out["chain_open_wall_ns"] - out["checkpoint_open_wall_ns"]
    out["extra_replay_ns"] = out["chain_replay_ns"] - out["checkpoint_replay_ns"]
    out["extra_footer_ns"] = out["chain_footer_ns"] - out["checkpoint_footer_ns"]
    out["extra_residual_ns"] = out["chain_residual_ns"] - out["checkpoint_residual_ns"]
    out["extra_replay_fraction"] = (
        out["extra_replay_ns"] / out["extra_open_wall_ns"]
        if out["extra_open_wall_ns"] > 0 else None)
    return out


def verdict(primary: dict, control: dict) -> str:
    raw = control["uninstrumented_penalty_ns"]
    traced = primary["extra_open_wall_ns"]
    if raw < 3_000_000:
        return "DELETE_NONMATERIAL"
    perturbation = control["penalty_perturbation_fraction"]
    if perturbation is None or perturbation > .15 or traced <= 0:
        return "INCONCLUSIVE_INSTRUMENTATION"
    share = primary["extra_replay_fraction"]
    if share is None or share < .60:
        return "DELETE_REPLAY_NOT_PROVEN_MAJOR"
    return "DELETE_REPLAY_MAJOR_COST_OWNER"


def run() -> None:
    root = Path(__file__).resolve().parents[1]
    for commit in (PARENT, PREREG):
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=root, check=True)
    identity = parent.parent.verify_source()
    destination = Path(os.environ.get("J24G65_RESULT", "evidence/j24g65-result.json"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).resolve()
    samples = []
    cases = {}
    env = dict(os.environ)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g65-") as td:
        stage = Path(td)
        cache = stage / "pycache"
        cache.mkdir()
        env["PYTHONPYCACHEPREFIX"] = str(cache)
        # Reuse one authentic public Writer generator and its existing physical
        # index/member/preflight court; do not author a second archive fixture.
        corpus = {
            n: parent.build_kind("delete", n, stage, destination.parent)
            for n in (512, 2048)
        }
        for n, depth in CASES:
            snap = corpus[n]["snapshots"][str(depth)]
            assert snap["expected_rows"] == n + 63 - depth
            assert len(snap["wire"]) == depth
            case = {k: v for k, v in snap.items() if k not in ("paths",)}
            cases[f"{n}/{depth}"] = case
            paths = {variant: Path(snap["paths"][variant])
                     for variant in ("chain", "checkpoint")}
            for block in range(BLOCKS):
                seq = (("chain", "checkpoint", "checkpoint", "chain") if
                       block % 2 == 0 else
                       ("checkpoint", "chain", "chain", "checkpoint"))
                for position, variant in enumerate(seq):
                    result = run_child(script, paths[variant], True, env)
                    assert result["rows"] == snap["expected_rows"]
                    assert result["depth"] == (depth if variant == "chain" else 0)
                    assert result["replay_calls"] == (
                        depth if variant == "chain" else 0)
                    assert result["footer_calls"] == (
                        depth + 1 if variant == "chain" else 1)
                    samples.append({
                        **result, "n": n, "depth_case": depth,
                        "variant": variant, "block": block,
                        "position": position,
                    })
            if (n, depth) == (2048, 63):
                for block in range(2):
                    seq = (("chain", "checkpoint", "checkpoint", "chain") if
                           block == 0 else
                           ("checkpoint", "chain", "chain", "checkpoint"))
                    for position, variant in enumerate(seq):
                        result = run_child(script, paths[variant], False, env)
                        assert result["rows"] == 2048
                        assert result["depth"] == (63 if variant == "chain" else 0)
                        assert result["replay_calls"] == result["footer_calls"] == 0
                        samples.append({
                            **result, "n": n, "depth_case": depth,
                            "variant": variant, "block": block,
                            "position": position,
                        })
        assert len(samples) == 72
        summaries = {f"{n}/{d}": summarise(samples, n, d) for n, d in CASES}
        primary = summaries["2048/63"]
        raw = [r for r in samples if
               r["n"] == 2048 and r["depth_case"] == 63
               and not r["instrumented"]]
        a = [r for r in raw if r["variant"] == "chain"]
        b = [r for r in raw if r["variant"] == "checkpoint"]
        assert len(a) == len(b) == 4
        uninstrumented_difference = median(a, "wall_ns") - median(b, "wall_ns")
        instrumented_difference = primary["extra_open_wall_ns"]
        control = {
            "uninstrumented_chain_ns": median(a, "wall_ns"),
            "uninstrumented_checkpoint_ns": median(b, "wall_ns"),
            "uninstrumented_penalty_ns": uninstrumented_difference,
            "instrumented_penalty_ns": instrumented_difference,
            "penalty_perturbation_fraction": (
                abs(uninstrumented_difference - instrumented_difference) /
                uninstrumented_difference
                if uninstrumented_difference > 0 else None),
        }
        decision = verdict(primary, control)
    report = {
        "claim_scope": "research-only public one-op DELETE physical journal cost attribution",
        "prereg_commit": PREREG, "parent_commit": PARENT,
        "source": identity, "python": platform.python_version(),
        "platform": platform.platform(), "cases": cases,
        "samples": samples, "summaries": summaries, "control": control,
        "decision": decision, "raw_samples_sha256": sha_samples(samples),
        "limitations": [
            "same-state checkpoint is a private oracle and adds archive bytes",
            "instrumented wall has wrapper overhead; independent stratum checks it",
            "fresh-child Reader open excludes interpreter import/startup but not warm filesystem cache",
            "original source is exact #805 parent and NOT released v0.30 main",
            "no product change, no native peak RSS or cold physical I/O",
            "no fsmeta-rich/hardlink recovery, full create/extract or ZIP/Zstd parity",
            "cross-generation mixed factoring is owned independently by #808",
        ],
    }
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("J24G65_HEAD", identity["head"])
    print("J24G65_DECISION", decision)
    print("J24G65_PRIMARY", json.dumps(primary, sort_keys=True))
    print("J24G65_CONTROL", json.dumps(control, sort_keys=True))
    print("J24G65_SAMPLES", len(samples))
    print("J24G65_RECEIPT_SHA256", parent.parent.sha256_file(destination))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--probe":
        print(json.dumps(
            probe(Path(sys.argv[2]), sys.argv[3] == "1"),
            sort_keys=True))
    else:
        run()
