#!/usr/bin/env python3
"""J24G69: preregistered same-input scientific cost comparison for two unmerged replay oracles.

Never a product source edit, release benchmark, or substitute for actual Reader timing.
"""
from __future__ import annotations

import copy
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
import tracemalloc

import msgpack
from cmpct.journal_replay import _apply_journal_ops as original

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
from j24g67_delete_bisect_onepass import new_candidate, compare as j67_compare

PARENT = "afdce3f3e598db402deba4c2dfde50a8de3f3e10"
PREREG = "4305d9a1f98ff6cf921bbe8ea24dd1dec2fa9de8"
COMPETITOR_HEAD = "41cd7f88d9fede55a495f36e78126b26eff85880"
COMPETITOR_BLOB = "7657a41d11f2b3c8136c0b69cfe62401f9b19ccb"
SIMPLE_BLOB = "dde3bbf0f4816adcfb552b83e579d8de09c86c19"
REPLAY_BLOB = "03743ca2a06c022c2ec64243a90fe373cf91e899"
D = 63
SHAPES = (2048, 8192, 32768)
PATTERNS = ("front", "middle", "tail")
BLOCKS = {2048: 8, 8192: 6, 32768: 4}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True, cwd=ROOT).strip()


def sha_obj(value) -> str:
    return hashlib.sha256(msgpack.packb(value, use_bin_type=True)).hexdigest()


def sha_json(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_competitor():
    path = ROOT / "evidence" / "j24g69-pinned-j24g64.py"
    data = path.read_bytes().replace(b"\r\n", b"\n")
    computed = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    assert computed == COMPETITOR_BLOB, ("competitor blob changed", computed)
    spec = importlib.util.spec_from_file_location("j24g69_pinned_general", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def custody():
    head = git("rev-parse", "HEAD")
    for ancestor in (PARENT, PREREG):
        subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, head],
                       cwd=ROOT, check=True)
    blobs = {"src/cmpct/journal_replay.py": REPLAY_BLOB,
             "research/j24g67_delete_bisect_onepass.py": SIMPLE_BLOB}
    for p, expected in blobs.items():
        got = git("rev-parse", "HEAD:" + p)
        assert got == expected, (p, got, expected)
    import cmpct.journal_replay as installed
    assert (ROOT / "src/cmpct/journal_replay.py").read_bytes().replace(b"\r\n", b"\n") == (
        Path(installed.__file__).read_bytes().replace(b"\r\n", b"\n"))
    return {"head": head, "parent": PARENT, "prereg": PREREG,
            "competitor_head": COMPETITOR_HEAD,
            "competitor_blob": COMPETITOR_BLOB,
            "simple_blob": SIMPLE_BLOB, "replay_blob": REPLAY_BLOB}


def build_case(n: int, pattern: str):
    names = [f"f{i:06d}.bin" for i in range(n + D)]
    base = {"files": [[v, 0, ["opaque-record", i, 0]] for i, v in enumerate(names)],
            "blobs": [], "fsmeta": {}}
    live = list(names)
    deltas = []
    for i in range(D):
        pos = 0 if pattern == "front" else len(live) - 1 if pattern == "tail" else len(live) // 2
        target = live.pop(pos)
        deltas.append({"blobs": [], "ops": [["del", target]]})
    assert len(live) == n and len(deltas) == D
    return base, deltas


def execute_simple(base, deltas, *, inspect=False):
    index = copy.deepcopy(base)
    copied = copy.deepcopy(deltas)
    apply, state = new_candidate()
    for delta in copied:
        index["blobs"].extend(delta["blobs"])
        apply(index, delta["ops"])
    counters = {k: v for k, v in state.items() if k != "index"}
    assert counters["optimized"] == D and counters["fallback"] == 0
    assert counters["admission_scans"] == 1
    return (index, counters) if inspect else index


def execute_general(competitor, base, deltas, *, inspect=False):
    index, route = competitor.factored(base, deltas)
    assert route == "factored", route
    return (index, {"route": route}) if inspect else index


def execute_original(competitor, base, deltas):
    return competitor.reference(base, deltas)


def sample(competitor, base, deltas, variant, n, pattern, block, position):
    gc.collect()
    w0, c0 = time.perf_counter_ns(), time.process_time_ns()
    if variant == "simple":
        result = execute_simple(base, deltas)
    else:
        result = execute_general(competitor, base, deltas)
    dt, cpu = time.perf_counter_ns() - w0, time.process_time_ns() - c0
    return {"n": n, "pattern": pattern, "block": block, "position": position,
            "variant": variant, "wall_ns": dt, "cpu_ns": cpu,
            "result_sha256": sha_obj(result)}


def peak_memory(competitor, base, deltas, variant):
    gc.collect()
    tracemalloc.start()
    try:
        result = (execute_simple(base, deltas) if variant == "simple"
                  else execute_general(competitor, base, deltas))
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return {"current_traced_bytes": current, "peak_traced_bytes": peak,
            "result_sha256": sha_obj(result)}


def edge_controls(competitor):
    rows = [["a", 0], ["b", 1], ["c", 2]]
    signed = {
        "files": copy.deepcopy(rows),
        "blobs": [],
        "fsmeta": {"xattrs": [[0, [[b"user.id", b"A"]]]],
                   "owner_overrides": [[0, 1000, 1000]]},
    }
    deltas = [{"blobs": [], "ops": [["del", "b"]]}]
    baseline = execute_original(competitor, signed, deltas)
    general, route = competitor.factored(signed, deltas)
    assert route == "factored" and general == baseline
    simple = copy.deepcopy(signed)
    apply, state = new_candidate()
    apply(simple, [["del", "b"]])
    assert state["fallback"] == 1 and state["optimized"] == 0
    assert simple == baseline
    unknown = {"files": copy.deepcopy(rows), "blobs": [], "fsmeta": {}}
    error = j67_compare(unknown, [[["future-op", "a"]]])["error"]
    assert error is not None
    assert competitor.compare(unknown, [{"blobs": [], "ops": [["future-op", "a"]]}]) == "matched-exception"
    return {"signed_fsmeta": {"general_route": route, "simple_fallback": 1,
                               "output_sha256": sha_obj(baseline)},
            "unknown_opcode": {"matched_error": error}}


def main():
    source = custody()
    competitor = load_competitor()
    controls = edge_controls(competitor)
    raw, cases = [], []
    for n in SHAPES:
        for pattern in PATTERNS:
            base, deltas = build_case(n, pattern)
            before = sha_obj([base, deltas])
            expected = execute_original(competitor, base, deltas)
            final_digest = sha_obj(expected)
            a, a_state = execute_simple(base, deltas, inspect=True)
            b, b_state = execute_general(competitor, base, deltas, inspect=True)
            assert a == expected and b == expected
            assert sha_obj(a) == sha_obj(b) == final_digest
            assert sha_obj([base, deltas]) == before
            for variant in ("simple", "factored"):
                # Warm-up is deliberately untimed; the input is unchanged.
                if variant == "simple":
                    execute_simple(base, deltas)
                else:
                    execute_general(competitor, base, deltas)
            for block in range(BLOCKS[n]):
                seq = ("simple", "factored", "factored", "simple") if block % 2 == 0 else (
                    "factored", "simple", "simple", "factored")
                for position, variant in enumerate(seq):
                    row = sample(competitor, base, deltas, variant, n, pattern, block, position)
                    assert row["result_sha256"] == final_digest
                    raw.append(row)
            mem = {v: peak_memory(competitor, base, deltas, v) for v in ("simple", "factored")}
            assert all(q["result_sha256"] == final_digest for q in mem.values())
            groups = {v: [x for x in raw if x["n"] == n and x["pattern"] == pattern
                          and x["variant"] == v] for v in ("simple", "factored")}
            assert all(len(v) == 2 * BLOCKS[n] for v in groups.values())
            simple_med = statistics.median(x["wall_ns"] for x in groups["simple"])
            general_med = statistics.median(x["wall_ns"] for x in groups["factored"])
            cases.append({
                "n": n, "pattern": pattern, "delta_depth": D, "blocks": BLOCKS[n],
                "initial_rows": n + D, "final_rows": n,
                "input_sha256": before, "index_sha256": final_digest,
                "median_wall_ns": {"simple": simple_med, "factored": general_med},
                "median_cpu_ns": {v: statistics.median(x["cpu_ns"] for x in groups[v])
                                  for v in groups},
                "factored_over_simple_wall_ratio": general_med / simple_med,
                "simple_over_factored_peak_traced_bytes":
                    mem["simple"]["peak_traced_bytes"] - mem["factored"]["peak_traced_bytes"],
                "memory": mem, "admission": {"simple": a_state, "factored": b_state},
            })
            print("CASE", n, pattern, "general/simple", round(general_med / simple_med, 4),
                  "peak_simple_minus_general", cases[-1]["simple_over_factored_peak_traced_bytes"],
                  flush=True)
    assert len(raw) == 3 * sum(BLOCKS.values()) * 4
    assert len(cases) == 9
    focus = next(x for x in cases if x["n"] == 2048 and x["pattern"] == "middle")
    ratio = focus["factored_over_simple_wall_ratio"]
    simple_peak = focus["memory"]["simple"]["peak_traced_bytes"]
    general_peak = focus["memory"]["factored"]["peak_traced_bytes"]
    host_direction = ("simple-edge" if ratio >= 1.20 and simple_peak - general_peak <= 1024 * 1024
                      else "general-near" if ratio <= 1.15 and general_peak - simple_peak <= 1024 * 1024
                      else "conditional")
    report = {
        "schema": "cmpct-j24g69-same-input-comparison-v1",
        "scope": "replay-mechanism lower-rung only; not Reader, product, or release",
        "source": source, "host": platform.platform(), "python": platform.python_version(),
        "controls": controls, "cases": cases, "raw": raw, "raw_sha256": sha_json(raw),
        "host_direction_not_crosshost_decision": host_direction,
        "limits": ["no physical signed archive produced; identical in-memory index and op inputs",
                   "no installed Reader A/B or source integration",
                   "tracemalloc is not resident memory",
                   "no disk IO, warm/cold open, recovery, hardlink restoration, full create/extract",
                   "no exported archive byte comparison, no ZIP/Zstd baseline"]
    }
    dest = Path(os.environ.get("J24G69_RESULT", "evidence/j24g69-result.json"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("J24G69_HEAD", source["head"])
    print("J24G69_RAW", len(raw), "CASE_COUNT", len(cases))
    print("J24G69_HOST_DIRECTION", host_direction)
    print("J24G69_RESULT_SHA256", hashlib.sha256(dest.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
