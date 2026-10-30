#!/usr/bin/env python3
"""J24G67 preregistered DELETE-only bisect oracle; no source or format modifications."""
from __future__ import annotations

import copy
import gc
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
import tracemalloc

import msgpack
from cmpct.builder import Builder
from cmpct import reader as reader_module
from cmpct import transactions
from cmpct.journal_replay import _apply_journal_ops as original_replay
from cmpct.validation import preflight_archive

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
import j24g63_public_put_delete_chain_court as inherited

BASE_SHA = "7f509d244325d4b6ea6d0e752ea365f79c33a742"
PREREG_SHA = "8b34b8a41cc890f0668fa944a245b80e6451dd3a"
SOURCE_BLOBS = {
    "src/cmpct/journal_replay.py": "03743ca2a06c022c2ec64243a90fe373cf91e899",
    "src/cmpct/reader.py": "29a8be64f3acfb027750351c6a567fd82cf7dc97",
    "src/cmpct/builder.py": "a2160a2f6b1ca3ef8cd94897cb68bb2fcb74ebc2",
    "src/cmpct/transactions.py": "3eef7fdc3f6deca5ddd6d9edf1292c7e2c864f11",
}
N, D, BLOCKS = 2048, 63, 8


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def source_attest() -> dict:
    head = git("rev-parse", "HEAD")
    for ancestor in (BASE_SHA, PREREG_SHA):
        subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, head],
                       cwd=ROOT, check=True)
    for path, expected in SOURCE_BLOBS.items():
        assert git("rev-parse", "HEAD:" + path) == expected, path
    import cmpct.journal_replay as jr
    for path, mod in ((ROOT / "src/cmpct/journal_replay.py", jr),
                      (ROOT / "src/cmpct/reader.py", reader_module),
                      (ROOT / "src/cmpct/transactions.py", transactions)):
        assert path.read_bytes().replace(b"\r\n", b"\n") == (
            Path(mod.__file__).read_bytes().replace(b"\r\n", b"\n"))
    assert reader_module._apply_journal_ops is original_replay
    return {"head": head, "baseline": BASE_SHA, "prereg": PREREG_SHA,
            "source_blobs": SOURCE_BLOBS}


def eligible_base(index: dict) -> bool:
    """Only monotone distinct strings and no positional per-member metadata."""
    if not isinstance(index, dict):
        return False
    rows = index.get("files")
    if not isinstance(rows, list):
        return False
    prev = None
    for row in rows:
        if not isinstance(row, list) or not row or not isinstance(row[0], str):
            return False
        if prev is not None and prev >= row[0]:
            return False
        prev = row[0]
    meta = index.get("fsmeta") or {}
    if not isinstance(meta, dict):
        return False
    if meta.get("xattrs") or meta.get("owner_overrides"):
        return False
    return True


def bisect_row(rows: list, path: str) -> int:
    lo, hi = 0, len(rows)
    while lo < hi:
        mid = (lo + hi) // 2
        if rows[mid][0] < path:
            lo = mid + 1
        else:
            hi = mid
    return lo


def new_candidate() -> tuple:
    """The first admitted operation establishes sorted-index ownership.

    A non-DELETE or failed eligibility disables this lightweight route for the
    remainder of the same replay chain; other indexes reset their admission.
    """
    state = {"index": None, "admitted": False, "disabled": False,
             "optimized": 0, "fallback": 0, "admission_scans": 0}

    def apply(index: dict, ops: list, *, max_files: int | None = None) -> dict:
        if state["index"] is not index:
            state["index"] = index
            state["admitted"] = False
            state["disabled"] = False
        if state["disabled"]:
            state["fallback"] += 1
            return original_replay(index, ops, max_files=max_files)
        if not state["admitted"]:
            state["admission_scans"] += 1
            if not eligible_base(index):
                state["disabled"] = True
                state["fallback"] += 1
                return original_replay(index, ops, max_files=max_files)
            state["admitted"] = True
        if (not isinstance(ops, list) or len(ops) != 1
                or not isinstance(ops[0], list) or len(ops[0]) != 2
                or ops[0][0] != "del" or not isinstance(ops[0][1], str)):
            state["disabled"] = True
            state["fallback"] += 1
            return original_replay(index, ops, max_files=max_files)
        rows = index["files"]
        pos = bisect_row(rows, ops[0][1])
        if pos >= len(rows) or rows[pos][0] != ops[0][1]:
            # Reader-valid public deletes have existing sources. Make missing
            # sources fall back, so noncanonical outside callers remain exact.
            state["disabled"] = True
            state["fallback"] += 1
            return original_replay(index, ops, max_files=max_files)
        rows.pop(pos)
        state["optimized"] += 1
        return index

    return apply, state


def run_reference(index: dict, generations: list[list]) -> dict:
    result = copy.deepcopy(index)
    for ops in copy.deepcopy(generations):
        original_replay(result, ops)
    return result


def run_candidate(index: dict, generations: list[list]) -> tuple[dict, dict]:
    result = copy.deepcopy(index)
    candidate, state = new_candidate()
    for ops in copy.deepcopy(generations):
        candidate(result, ops)
    return result, {k: v for k, v in state.items() if k != "index"}


def compare(index: dict, generations: list[list]) -> dict:
    source = msgpack.packb([index, generations], use_bin_type=True)
    before = hashlib.sha256(source).hexdigest()
    error_original = error_candidate = None
    try:
        original = run_reference(index, generations)
    except Exception as exc:
        original = None
        error_original = (type(exc).__name__, str(exc))
    try:
        candidate, stats = run_candidate(index, generations)
    except Exception as exc:
        candidate, stats = None, {}
        error_candidate = (type(exc).__name__, str(exc))
    assert error_original == error_candidate, (error_original, error_candidate)
    assert original == candidate
    if original is not None:
        assert msgpack.packb(original, use_bin_type=True) == (
            msgpack.packb(candidate, use_bin_type=True))
    assert hashlib.sha256(msgpack.packb(
        [index, generations], use_bin_type=True)).hexdigest() == before
    return {"error": error_original, "stats": stats}


def hostile_differentials() -> dict:
    base_rows = [[f"f{i:03d}", 0, ["row", i]] for i in range(16)]
    result = {}
    cases = {
        "valid-delete": ({"files": copy.deepcopy(base_rows)}, [[["del", "f003"]]]),
        "missing-delete": ({"files": copy.deepcopy(base_rows)}, [[["del", "absent"]]]),
        "duplicate-names": ({"files": copy.deepcopy(base_rows) + [copy.deepcopy(base_rows[-1])]},
                             [[["del", "f003"]]]),
        "unsorted": ({"files": list(reversed(copy.deepcopy(base_rows)))},
                     [[["del", "f003"]]]),
        "xattrs": ({"files": copy.deepcopy(base_rows),
                    "fsmeta": {"xattrs": [[3, [[b"user.tag", b"x"]]]] }},
                   [[["del", "f003"]]]),
        "owners": ({"files": copy.deepcopy(base_rows),
                   "fsmeta": {"owner_overrides": [[3, 2000, 2001]]}},
                   [[["del", "f003"]]]),
        "malformed": ({"files": copy.deepcopy(base_rows)}, [[["del", 42]]]),
        "unknown": ({"files": copy.deepcopy(base_rows)}, [[["future", "f003"]]]),
        "multi": ({"files": copy.deepcopy(base_rows)},
                  [[["del", "f003"], ["del", "f004"]]]),
        "delete-then-put": ({"files": copy.deepcopy(base_rows)},
                            [[["del", "f003"]], [["put", ["f003", 9]]]]),
        "rename": ({"files": copy.deepcopy(base_rows)}, [[["ren", "f003", "zz"]]]),
        "delete-all": ({"files": copy.deepcopy(base_rows)},
                       [[["del", f"f{i:03d}"]] for i in range(16)]),
    }
    for name, (base, generations) in cases.items():
        try:
            got = compare(base, generations)
        except Exception as exc:
            raise AssertionError(f"{name}: {exc}") from exc
        result[name] = got
    assert result["valid-delete"]["stats"]["optimized"] == 1
    assert result["delete-all"]["stats"]["optimized"] == 16
    for name in ("missing-delete", "duplicate-names", "unsorted",
                 "xattrs", "owners", "malformed", "unknown", "multi",
                 "delete-then-put", "rename"):
        assert result[name]["stats"]["fallback"] > 0, name
    # Deterministic scattered deletions across a sorted namespace, including
    # first/middle/last and repeated absent names; no borrowed fixture identity.
    for seed in range(500):
        rows = [[f"p{i:04d}", seed, ["opaque", i]] for i in range(4 + seed % 43)]
        live = [r[0] for r in rows]
        ops = []
        for step in range(min(16, len(live))):
            target = live.pop((seed * 7 + step * 17) % len(live))
            ops.append([["del", target]])
        compare({"files": rows}, ops)
    return {"named": result, "randomized_sequences": 500}


def physical_archive(stage: Path) -> tuple[Path, dict]:
    source = stage / "source"
    source.mkdir()
    for i in range(N + D):
        (source / f"f{i:04d}.dat").write_bytes(inherited.content("base", i))
    archive = stage / "j24g67-authentic-delete.cmpct"
    t0 = time.perf_counter()
    Builder(source, workers=1, reproducible=True).build(archive)
    targets = inherited.target_names("delete", N)
    for name in targets:
        transactions.append_delete(archive, name)
    build_wall = time.perf_counter() - t0
    wire = inherited.signed_ledger(archive, "delete", D, targets)
    with reader_module.CMPCT(archive) as ar:
        assert ar.delta_depth == D
        assert len(ar.files) == N
        assert ar.verify() == N
        original = msgpack.packb(ar.index, use_bin_type=True)
        index_sha = hashlib.sha256(original).hexdigest()
        assert "fsmeta" not in ar.index or not ar.index["fsmeta"].get("xattrs")
        for i, row in enumerate(ar.files):
            assert isinstance(row[0], str)
            assert ar.read(row[0]) == inherited.content("base", int(row[0][1:5]))
    pre = preflight_archive(archive)
    assert pre["files"] == N and pre["delta_depth"] == D
    return archive, {"sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                     "archive_bytes": archive.stat().st_size,
                     "logical_bytes": N * len(inherited.content("base", 0)),
                     "build_and_writer_wall_s": build_wall,
                     "footers": len(wire) + 1,
                     "delta_operations": len(wire),
                     "index_sha256": index_sha,
                     "preflight": pre}


def reader_open(archive: Path, variant: str) -> tuple[dict, dict]:
    old = reader_module._apply_journal_ops
    state = {}
    if variant == "candidate":
        fun, state = new_candidate()
        reader_module._apply_journal_ops = fun
    try:
        gc.collect()
        t0, c0 = time.perf_counter_ns(), time.process_time_ns()
        with reader_module.CMPCT(archive) as ar:
            wall, cpu = time.perf_counter_ns() - t0, time.process_time_ns() - c0
            assert ar.delta_depth == D and len(ar.files) == N
            digest = hashlib.sha256(msgpack.packb(ar.index, use_bin_type=True)).hexdigest()
        return {"variant": variant, "open_wall_ns": wall, "open_cpu_ns": cpu,
                "index_sha256": digest}, {
                    k: v for k, v in state.items() if k != "index"}
    finally:
        reader_module._apply_journal_ops = old


def main() -> None:
    identity = source_attest()
    output = Path(os.environ.get("J24G67_RESULT", "evidence/j24g67-result.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    hostile = hostile_differentials()
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g67-") as d:
        stage = Path(d)
        archive, physical = physical_archive(stage)
        raw = []
        for block in range(BLOCKS):
            seq = ("reference", "candidate", "candidate", "reference") if (
                block % 2 == 0) else (
                "candidate", "reference", "reference", "candidate")
            for pos, variant in enumerate(seq):
                measured, state = reader_open(archive, variant)
                assert measured["index_sha256"] == physical["index_sha256"]
                if variant == "candidate":
                    assert state["optimized"] == D, state
                    assert state["fallback"] == 0, state
                    assert state["admission_scans"] == 1, state
                raw.append({"block": block, "position": pos, **measured,
                            "replay": state})
        assert len(raw) == BLOCKS * 4
        a = [x for x in raw if x["variant"] == "reference"]
        b = [x for x in raw if x["variant"] == "candidate"]
        assert len(a) == len(b) == 16
        base = statistics.median(x["open_wall_ns"] for x in a)
        fast = statistics.median(x["open_wall_ns"] for x in b)
        saving = base - fast
        speedup = base / fast
        decision = "SURVIVES" if speedup >= 2.0 and saving >= 3_000_000 else "BELOW_HURDLE"
        # Isolated tracked memory is separate from the uninstrumented timing
        # court; tracemalloc does not measure OS resident memory.
        tracemalloc.start()
        _, state = reader_open(archive, "candidate")
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert state["optimized"] == D
        final = {
            "claim": "research-only sorted DELETE-onepass Reader-open micro/product-seam court",
            "identity": identity, "platform": platform.platform(),
            "python": platform.python_version(), "physical": physical,
            "hostile": hostile, "raw": raw,
            "raw_sha256": hashlib.sha256(json.dumps(raw, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest(),
            "median_reference_wall_ns": base,
            "median_candidate_wall_ns": fast,
            "median_reference_cpu_ns": statistics.median(x["open_cpu_ns"] for x in a),
            "median_candidate_cpu_ns": statistics.median(x["open_cpu_ns"] for x in b),
            "speedup": speedup, "saving_wall_ns": saving, "decision": decision,
            "candidate_tracemalloc_peak_bytes": peak_bytes,
            "limits": ["research monkeypatch only, no product source modification",
                       "no sparse xattrs or hardlink identity",
                       "process/import startup outside timer; warm filesystem cache",
                       "tracemalloc not RSS; source-exact original archive bytes",
                       "no complete create/extract/read/selective or release matrix"]
        }
        # Preserve the exact same physical archive alongside the receipt, even
        # on negative speed evidence. It is tiny enough for standard artifacts.
        physical_path = output.parent / "j24g67-authentic-delete.cmpct"
        shutil.copyfile(archive, physical_path)
        assert hashlib.sha256(physical_path.read_bytes()).hexdigest() == physical["sha256"]
    output.write_text(json.dumps(final, sort_keys=True, indent=2) + "\n")
    print("J24G67_HEAD", identity["head"])
    print("J24G67_RESULT", decision, "speedup", speedup, "saving_ms", saving / 1e6)
    print("J24G67_ARCHIVE_BYTES", physical["archive_bytes"])
    print("J24G67_OBSERVATIONS", len(raw))
    print("J24G67_RESULT_SHA256",
          hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
