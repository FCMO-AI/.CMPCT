#!/usr/bin/env python3
"""J24G62: research-only no-byte cross-generation rename factoring oracle.

Uses real Builder/public Writer archives and compares *replay only*. Does not
modify or monkeypatch CMPCT Reader, journal admission, Writer, or format.
"""
from __future__ import annotations

import copy
import gc
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import sys
import tempfile
import time
import tracemalloc

import msgpack
from cmpct.builder import Builder
from cmpct.journal_replay import _apply_journal_ops, _validate_journal_ops
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from j24g60_single_delta_chain_court import (
    footer_chain, make_case, sha256_file, verify_source,
)

N = 2048
DEPTH = 63
BLOCKS = 8
SOURCE_PARENT = "fb5d96cdb8855fe3e01868792e65b79d3d61661d"
PREREG = "13bfa4574fd56af39475f3cb9e3bd5f64e06e148"


def original_replay(base: dict, deltas: list[dict]) -> dict:
    idx = copy.deepcopy(base)
    for delta in deltas:
        idx["blobs"].extend(copy.deepcopy(delta.get("blobs", [])))
        _apply_journal_ops(idx, copy.deepcopy(delta.get("ops", [])))
    return idx


def _eligible(base: dict, deltas: list[dict]) -> tuple[bool, str]:
    """Pure admission. Do not touch input or weaken per-op grammar."""
    rows = base["files"]
    names = [row[0] for row in rows]
    if len(names) != len(set(names)):
        return False, "duplicate-base-path"
    fsmeta = base.get("fsmeta") or {}
    if fsmeta.get("xattrs") or fsmeta.get("owner_overrides"):
        return False, "positional-metadata"
    if not deltas:
        return False, "no-deltas"
    live = set(names)
    for delta in deltas:
        ops = delta.get("ops", [])
        _validate_journal_ops(ops)
        if len(ops) != 1 or ops[0][0] != "ren":
            return False, "non-one-rename-generation"
        _tag, old, new = ops[0]
        if old not in live:
            # The original silently ignores a missing source; no reason to
            # extend optimized admission into hostile/ill-formed histories.
            return False, "missing-source"
        if new != old and new in live:
            return False, "rename-collision"
        live.remove(old)
        live.add(new)
    return True, "one-op-disjoint-renames"


def factored_replay(base: dict, deltas: list[dict]) -> tuple[dict, str]:
    allowed, reason = _eligible(base, deltas)
    if not allowed:
        return original_replay(base, deltas), "fallback:" + reason
    idx = copy.deepcopy(base)
    by_name = {row[0]: row for row in idx["files"]}
    # The original base row identities and sparse fsmeta (if present) never
    # change; sparse positional records are excluded by the admission above.
    for delta in deltas:
        idx["blobs"].extend(copy.deepcopy(delta.get("blobs", [])))
        _tag, old, new = delta["ops"][0]
        if new != old:
            row = by_name.pop(old)
            row[0] = new
            by_name[new] = row
    idx["files"][:] = sorted(by_name.values(), key=lambda row: row[0])
    return idx, "factored"


def _observe(base, deltas, kind):
    gc.collect()
    wall0 = time.perf_counter_ns()
    cpu0 = time.process_time_ns()
    if kind == "baseline":
        output = original_replay(base, deltas)
        route = "original"
    else:
        output, route = factored_replay(base, deltas)
    cpu = time.process_time_ns() - cpu0
    wall = time.perf_counter_ns() - wall0
    return output, {"variant": kind, "wall_ns": wall, "cpu_ns": cpu, "route": route}


def read_wire(path: Path) -> tuple[dict, list[dict]]:
    # The independently framed and SHA-authenticated physical oracle runs first.
    physical = footer_chain(path)
    assert len(physical) == DEPTH + 1
    assert all(item["op_width"] == 1 for item in physical[:-1])
    reversed_deltas = []
    with CMPCT(path) as ar:
        pos = ar.latest_footer_pos
        while pos:
            record = ar._decode_generation_payload(pos)
            assert record is not None
            kind, payload, previous = record
            document = msgpack.unpackb(payload, raw=False)
            if kind == 0:
                return document, list(reversed(reversed_deltas))
            assert kind == 1
            reversed_deltas.append(document)
            pos = previous
    raise AssertionError("no authenticated checkpoint in physical chain")


def differential_cases() -> dict:
    rng = random.Random(0xC0622026)
    outcomes = {}
    for case in range(2200):
        size = rng.randrange(2, 40)
        names = [f"f{i:03d}" for i in range(size)]
        rows = [[n, i] for i, n in enumerate(names)]
        fsmeta = {"owner": [0, 0], "owner_overrides": [], "xattrs": []}
        category = case % 11
        if category == 2:
            fsmeta["xattrs"] = [[rng.randrange(size), [[b"user.unit", b"truth"]]]]
        elif category == 3:
            fsmeta["owner_overrides"] = [[rng.randrange(size), 1001, 1002]]
        elif category == 4:
            fsmeta["owner_overrides"] = [[size + 1, 1001, 1002]]
        elif category == 5:
            rows.append(copy.deepcopy(rows[-1]))
        base = {"files": rows, "blobs": [], "fsmeta": fsmeta}
        deltas = []
        live = set(names)
        for step in range(rng.randrange(1, 16)):
            old = rng.choice(tuple(sorted(live))) if live else "missing"
            if category == 6 and step == 1:
                op = ["del", old]
            elif category == 7 and step == 1:
                op = ["put", [old, -step]]
            elif category == 8 and step == 1:
                op = ["ren", old, rng.choice(tuple(sorted(live)))]
            elif category == 9 and step == 1:
                op = ["ren", "source-does-not-exist", "new"]
            elif category == 10 and step == 1:
                op = ["not-an-op", old]
            else:
                new = f"new_{case:04d}_{step:03d}"
                op = ["ren", old, new]
                if old in live:
                    live.remove(old)
                    live.add(new)
            deltas.append({"blobs": [], "ops": [op]})
        frozen = copy.deepcopy(base)
        try:
            expected = original_replay(base, deltas)
            prior_error = None
        except Exception as err:
            expected = None
            prior_error = (type(err), str(err))
        try:
            observed, route = factored_replay(base, deltas)
            new_error = None
        except Exception as err:
            observed = None
            new_error = (type(err), str(err))
            route = "exception"
        assert prior_error == new_error, (case, category, prior_error, new_error)
        assert observed == expected, (case, category, route)
        assert base == frozen, ("oracle mutated caller input", case)
        key = route if new_error is None else "matched-exception"
        outcomes[key] = outcomes.get(key, 0) + 1
    assert sum(outcomes.values()) == 2200
    assert outcomes.get("factored", 0) > 0
    assert outcomes.get("matched-exception", 0) > 0
    return outcomes


def main():
    source = verify_source()
    differential = differential_cases()
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g62-") as temp:
        stage = Path(temp)
        corpus = stage / "source"
        corpus.mkdir()
        for i in range(N):
            (corpus / f"f{i:04d}.dat").write_bytes(
                hashlib.sha256(f"generic-record-{i}".encode()).digest() * 2
            )
        snapshots = make_case(corpus, stage, N)
        physical = snapshots[str(DEPTH)]
        chain = Path(physical["paths"]["chain"])
        checkpoint = Path(physical["paths"]["checkpoint"])
        before_sha = sha256_file(chain)
        base, deltas = read_wire(chain)
        assert len(deltas) == DEPTH
        expected = original_replay(base, deltas)
        observed, route = factored_replay(base, deltas)
        assert route == "factored", route
        assert observed == expected, "physical signed-history final index mismatch"
        assert msgpack.packb(observed, use_bin_type=True) == msgpack.packb(
            expected, use_bin_type=True
        ), "bytewise MessagePack index mismatch"
        with CMPCT(chain) as ar, CMPCT(checkpoint) as snap:
            assert ar.index == expected == snap.index
            assert ar.verify() == N and snap.verify() == N
            assert sorted(ar.by) == sorted(snap.by)
        assert preflight_archive(chain)["files"] == N
        assert sha256_file(chain) == before_sha
        assert chain.stat().st_size == physical["archive_bytes"]["chain"]
        # Separate stratum for timing: do not run tracemalloc during wall/CPU.
        samples = []
        for block in range(BLOCKS):
            seq = ("baseline", "factored", "factored", "baseline") if block % 2 == 0 else (
                "factored", "baseline", "baseline", "factored"
            )
            for phase, kind in enumerate(seq):
                outcome, observation = _observe(base, deltas, kind)
                assert outcome == expected
                samples.append({"block": block, "phase": phase, **observation})
        memory = {}
        for kind in ("baseline", "factored"):
            gc.collect()
            tracemalloc.start()
            outcome = (
                original_replay(base, deltas) if kind == "baseline"
                else factored_replay(base, deltas)[0]
            )
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            assert outcome == expected
            memory[kind] = {"peak_traced_bytes": peak, "retained_traced_bytes": current}
        a = [row for row in samples if row["variant"] == "baseline"]
        b = [row for row in samples if row["variant"] == "factored"]
        med_a = statistics.median(row["wall_ns"] for row in a)
        med_b = statistics.median(row["wall_ns"] for row in b)
        med_acpu = statistics.median(row["cpu_ns"] for row in a)
        med_bcpu = statistics.median(row["cpu_ns"] for row in b)
        overhead = memory["factored"]["peak_traced_bytes"] - memory["baseline"]["peak_traced_bytes"]
        decision = ("BOUNDED_RENAME_FACTORIZATION_SEED" if
                    med_b > 0 and med_a / med_b >= 3 and overhead <= 2 * 1024 * 1024
                    else "NO_BOUNDED_RENAME_FACTORIZATION_WIN")
        report = {
            "schema": "cmpct-j24g62-research-v1",
            "scope": "research-only signed-history replay; no Reader/product performance credit",
            "status": decision,
            "source": source,
            "prereg_commit": PREREG,
            "parent_research_head": SOURCE_PARENT,
            "host": platform.platform(),
            "python": platform.python_version(),
            "members": N,
            "generations": DEPTH,
            "samples": samples,
            "differential": differential,
            "observed_route": route,
            "wall_median_ns": {"baseline": med_a, "factored": med_b},
            "cpu_median_ns": {"baseline": med_acpu, "factored": med_bcpu},
            "wall_speedup": med_a / med_b,
            "cpu_speedup": med_acpu / med_bcpu if med_bcpu else None,
            "tracemalloc": memory,
            "extra_peak_traced_bytes": overhead,
            "physical_archive_sha256": before_sha,
            "complete_archive_bytes": physical["archive_bytes"],
            "checkpoint_premium_bytes": physical["checkpoint_premium_bytes"],
            "limitations": [
                "No added archive bytes in research algorithm; checkpoint is extra-byte oracle",
                "Does not install into Reader or alter published r24",
                "Only authentic single-rename no-collision chains without sparse positional fsmeta",
                "CPU/wall measures helper replay, not decode, import, cold disk, create or extract",
                "Tracemalloc measures Python tracing, not peak process RSS",
                "Mixed operations and signed sparse metadata always route to original baseline",
                "No recovery/fuzz/native ABI or complete official release parity",
            ],
        }
    dest = Path(os.environ.get("J24G62_RESULT", "evidence/j24g62-result.json"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("J24G62_DECISION", decision)
    print("J24G62_SPEEDUP", round(report["wall_speedup"], 4))
    print("J24G62_EXTRA_PEAK_TRACED_BYTES", overhead)
    print("J24G62_DIFFERENTIAL", json.dumps(differential, sort_keys=True))
    print("J24G62_RAW_SHA256", sha256_file(dest))
    print("J24G62_HEAD", source["head"])


if __name__ == "__main__":
    main()
