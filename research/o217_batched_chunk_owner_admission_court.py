"""O217: source-bound 4-arm strict S_CHUNKS validator multiplicity ownership falsifier.

No product source edits or release claims. The 'unguarded' control is explicitly a performance
oracle ONLY and must never be promoted as safe admission. Original validator is the authority; exact input/type/size law remains intact.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import inspect
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tempfile
import time

import cmpct.reader as reader_mod
import cmpct.validation as validation
from cmpct.codec import K_FILE, S_CHUNKS
from cmpct.reader import CMPCT

ORIGINAL = validation._validate_storage
METHODS = ("original", "fast", "batched", "unguarded")
SHAPES = (("one-ref", 1, 1), ("repeated-4096", 4096, 1), ("repeated-65536", 65536, 1), ("repeated-262144", 262144, 1), ("mixed-256-65536", 65536, 256), ("distinct-4096", 4096, 4096))
REPEATS = 5
CYCLES = 3
SOURCE_VALIDATOR_BLOB = "51c2849061f99a4afeddb7666956b24566ce7de0"


def fast_validate(path, kind, size, storage, blobs, recipes):
    if kind == K_FILE and isinstance(storage, list) and storage and storage[0] == S_CHUNKS:
        if len(storage) != 2 or not isinstance(storage[1], list):
            raise validation.ValidationError(f"file {path!r} has malformed chunk storage")
        blob_count = len(blobs)
        total = 0
        for ci, idx in enumerate(storage[1]):
            # On a serialized built-in int, defer label construction and _ref() call.
            # Fallback to the ORIGINAL _ref on any invalid/unusual type or range.
            if type(idx) is not int or idx < 0 or idx >= blob_count:
                idx = validation._ref(idx, blob_count, f"file {path!r} chunk {ci}")
            total += blobs[idx][1]
        if total != size:
            raise validation.ValidationError(f"file {path!r} chunk lengths do not equal logical size")
        return None
    return ORIGINAL(path, kind, size, storage, blobs, recipes)


def batched_validate(path, kind, size, storage, blobs, recipes):
    """Count all exact built-in integer references; reject all anomalies via original court.

    Counter owns the repeated-reference traversal and multiplicity aggregation. There is
    still an O(N) type scan; this is never a shortcut around strict per-reference admission.
    """
    if kind == K_FILE and isinstance(storage, list) and storage and storage[0] == S_CHUNKS:
        if len(storage) != 2 or not isinstance(storage[1], list):
            raise validation.ValidationError(f"file {path!r} has malformed chunk storage")
        refs = storage[1]
        # A bool hashes like int 0/1. Avoid silently merging aliases by requiring the
        # exact MessagePack-deserialized primitive int for EVERY element, not a sample.
        if not all(type(idx) is int for idx in refs):
            return ORIGINAL(path, kind, size, storage, blobs, recipes)
        multiplicity = collections.Counter(refs)
        if multiplicity and (min(multiplicity) < 0 or max(multiplicity) >= len(blobs)):
            # The first bad reference's exact index/message is owned by ORIGINAL.
            return ORIGINAL(path, kind, size, storage, blobs, recipes)
        total = sum(blobs[idx][1] * count for idx, count in multiplicity.items())
        if total != size:
            raise validation.ValidationError(f"file {path!r} chunk lengths do not equal logical size")
        return None
    return ORIGINAL(path, kind, size, storage, blobs, recipes)


def unguarded_oracle(path, kind, size, storage, blobs, recipes):
    if kind == K_FILE and isinstance(storage, list) and storage and storage[0] == S_CHUNKS:
        return None  # Unsafe control: timing lower bound ONLY.
    return ORIGINAL(path, kind, size, storage, blobs, recipes)


def install(mode):
    validation._validate_storage = {"original": ORIGINAL, "fast": fast_validate, "batched": batched_validate,
                                    "unguarded": unguarded_oracle}[mode]


def outcome(fn, path, kind, size, storage, blobs):
    try:
        fn(path, kind, size, storage, blobs, [])
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "type": type(exc).__name__, "message": str(exc)}


def semantics_court():
    """Failure kinds and messages must exactly match the real unchanged validator."""
    blobs = [[0, 4, 4, 0, 0], [0, 7, 7, 0, 0]]
    cases = [
        ("valid-single", 4, [S_CHUNKS, [0]]),
        ("valid-duplicate", 15, [S_CHUNKS, [0, 1, 0]]),
        ("valid-empty", 0, [S_CHUNKS, []]),
        ("short-total", 5, [S_CHUNKS, [0]]),
        ("long-total", 3, [S_CHUNKS, [0]]),
        ("bad-neg", 4, [S_CHUNKS, [-1]]),
        ("bad-outside", 4, [S_CHUNKS, [2]]),
        ("bad-bool", 4, [S_CHUNKS, [True]]),
        ("bad-float", 4, [S_CHUNKS, [0.0]]),
        ("bad-string", 4, [S_CHUNKS, ["0"]]),
        ("bad-none", 4, [S_CHUNKS, [None]]),
        ("bad-map", 4, [S_CHUNKS, {"0": 0}]),
        ("bad-missing", 4, [S_CHUNKS]),
        ("bad-surplus", 4, [S_CHUNKS, [0], 1]),
        ("bad-sublist", 4, [S_CHUNKS, [[0]]]),
        ("bad-late", 12, [S_CHUNKS, [0, 0, True]]),
        ("bad-late-bound", 12, [S_CHUNKS, [0, 0, -1]]),
        ("valid-heavy", 4 * 4096, [S_CHUNKS, [0] * 4096]),
        ("invalid-heavy-tail", 4 * 4096, [S_CHUNKS, [0] * 4095 + [False]]),
    ]
    results = []
    for name, size, storage in cases:
        a = outcome(ORIGINAL, "f", K_FILE, size, storage, blobs)
        b = outcome(fast_validate, "f", K_FILE, size, storage, blobs)
        assert a == b, (name, a, b)
        c = outcome(batched_validate, "f", K_FILE, size, storage, blobs)
        assert a == c, (name, a, c)
        results.append({"case": name, "outcome": a})
    # Entrypoint isolation: no changes for other representation/storage tags.
    for kind, storage in [(K_FILE, [123, 0]), (K_FILE, []), (K_FILE, "bad"), (0, None)]:
        a = outcome(ORIGINAL, "other", kind, 4, storage, blobs)
        b = outcome(fast_validate, "other", kind, 4, storage, blobs)
        assert a == b, (kind, storage, a, b)
        c = outcome(batched_validate, "other", kind, 4, storage, blobs)
        assert a == c, (kind, storage, a, c)
    # Different blob sizes and identities, repeated owners, and a late invalid owner.
    for name, size, refs in [
        ("mixed-positive", 29, [0, 1, 1, 1, 0]),
        ("mixed-under", 28, [0, 1, 1, 1, 0]),
        ("mixed-outside", 29, [0, 1, 2, 1, 0]),
        ("mixed-late-bool", 29, [0, 1, 1, 1, True]),
        ("mixed-late-float", 29, [0, 1, 1, 1, 0.0]),
        ("mixed-late-negative", 29, [0, 1, 1, 1, -1]),
    ]:
        storage = [S_CHUNKS, refs]
        a = outcome(ORIGINAL, "f", K_FILE, size, storage, blobs)
        b = outcome(fast_validate, "f", K_FILE, size, storage, blobs)
        c = outcome(batched_validate, "f", K_FILE, size, storage, blobs)
        assert a == b == c, (name, a, b, c)
        results.append({"case": name, "outcome": a})
    return results


def worker(path, logical_size, mode, runs):
    assert mode in METHODS
    reader_source = Path(inspect.getfile(reader_mod)).resolve()
    validation_source = Path(inspect.getfile(validation)).resolve()
    origin_hash = hashlib.sha256(reader_source.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    val_hash = hashlib.sha256(validation_source.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    install(mode)
    with CMPCT(Path(path)) as rd:
        assert len(rd.files) == 1 and rd.files[0][4] == logical_size
        # A first-range test exercises actual Reader semantic equivalence on valid input.
        assert rd.read_range("fixed.bin", 0, min(4, logical_size)) == b"ABCD"[:min(4, logical_size)]
    wall, cpu = [], []
    for _ in range(runs):
        t0, c0 = time.perf_counter_ns(), time.process_time_ns()
        with CMPCT(Path(path)) as rd:
            assert len(rd.files) == 1 and rd.files[0][4] == logical_size
        wall.append(time.perf_counter_ns() - t0)
        cpu.append(time.process_time_ns() - c0)
    print(json.dumps({"mode": mode, "reader_source_sha256": origin_hash,
                      "validation_source_sha256": val_hash, "wall_ns": wall,
                      "cpu_ns": cpu, "path": str(reader_source),
                      "python": sys.version, "platform": sys.platform}, sort_keys=True))


def controller(out_path):
    repo = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).resolve().parents[1])).resolve()
    # The pre-existing O215 fixture is source-independent of Builder.
    sys.path.insert(0, str(repo / "tests"))
    from test_o215_fixed_chunk_admission import _make_archive

    blob = subprocess.check_output(["git", "rev-parse", "HEAD:src/cmpct/validation.py"], cwd=repo, text=True).strip()
    assert blob == SOURCE_VALIDATOR_BLOB, ("validator drift; reread actual semantics", blob)
    cases = semantics_court()
    rng = random.Random(216)
    all_rows = []
    with tempfile.TemporaryDirectory(prefix="o217-r24-oracle-") as td:
        root = Path(td)
        for name, n, distinct in SHAPES:
            if distinct == 1:
                refs = [0] * n
                blobs = (b"ABCD",)
                logical = b"ABCD" * n
            else:
                # Deterministic held-out diverse ownership; no identity-based admission policy.
                blobs = tuple(b"ABCD" + j.to_bytes(2, "little") for j in range(distinct))
                refs = [j % distinct for j in range(n)]
                logical = b"".join(blobs[j] for j in refs)
            content = _make_archive(refs, logical, blobs=blobs)
            path = root / f"{name}.cmpct"
            path.write_bytes(content)
            observations = []
            for cycle in range(CYCLES):
                # Paired randomized ordering rather than one systematic warm-cache advantage.
                arms = list(METHODS) * 2
                rng.shuffle(arms)
                for mode in arms:
                    command = [sys.executable, str(Path(__file__).resolve()),
                               "--worker", str(path), str(len(logical)), mode, str(REPEATS)]
                    completed = subprocess.run(command, cwd=td, text=True, capture_output=True,
                                               timeout=120, check=True)
                    x = json.loads(completed.stdout.strip())
                    assert x["mode"] == mode
                    x["cycle"] = cycle
                    observations.append(x)
            summary = {}
            for mode in METHODS:
                rows = [x for x in observations if x["mode"] == mode]
                summary[mode] = {
                    "median_worker_wall_ns": statistics.median(statistics.median(x["wall_ns"]) for x in rows),
                    "median_worker_cpu_ns": statistics.median(statistics.median(x["cpu_ns"]) for x in rows)
                }
            base, fast, batched, none = (summary[v]["median_worker_wall_ns"] for v in METHODS)
            elapsed_gain = base / fast
            batch_over_fast = fast / batched
            batch_over_unsafe = batched / none
            debt_ratio = fast / none
            debt_abs_ms = (fast - none) / 1e6
            debt = debt_ratio > 2 and ((n == 65536 and debt_abs_ms > 5)
                                        or (n == 262144 and debt_abs_ms > 20))
            print(f"O217_PROFILE={name} REFS={n} DISTINCT={distinct} FAST_V_BATCH={batch_over_fast:.3f}x "
                  f"BATCH_V_UNGUARDED={batch_over_unsafe:.3f}x BASE_V_FAST={elapsed_gain:.3f}x FAST_V_UNGUARDED={debt_ratio:.3f}x "
                  f"FAST_EXTRA_MS={debt_abs_ms:.3f} STILL_DEBT={debt}", flush=True)
            all_rows.append({"count": n, "profile": name, "distinct": distinct, "archive_bytes": len(content),
                             "archive_sha256": hashlib.sha256(content).hexdigest(),
                             "observations": observations, "summary": summary,
                             "baseline_to_fast_ratio": elapsed_gain,
                             "fast_to_batched_ratio": batch_over_fast,
                             "batched_to_unguarded_ratio": batch_over_unsafe,
                             "fast_to_unguarded_oracle_ratio": debt_ratio,
                             "fast_extra_wall_ms": debt_abs_ms, "still_material_debt": debt})
    semantic_ok = True
    repeated = [x for x in all_rows if x["distinct"] == 1 and x["count"] >= 65536]
    gain = all(x["fast_to_batched_ratio"] >= 1.25 for x in repeated)
    diverse = [x for x in all_rows if x["distinct"] > 1]
    severe_diverse = any(x["fast_to_batched_ratio"] < 0.70 for x in diverse)
    # Reject an attractive repetitive special case if the high-diversity structural control
    # collapses; retain BOTH negatives rather than averaging them away.
    classification = ("BATCHED_REF_SEMANTICS_MATCH_AND_HIGH_N_GAIN" if gain and not severe_diverse
                      else "BATCHED_REF_OWNER_COUNTER_INSUFFICIENT_OR_NARROW")
    result = {"classification": classification, "semantic_equivalence": semantic_ok,
              "high_n_strict_gain_predicate": gain, "diverse_regression_predicate": severe_diverse,
              "science_only": True, "unguarded": "unsafe lower bound ONLY",
              "source_o216": "research/o216_fixed_chunk_validator_fastpath_oracle.py@7002fe2db2bfc41fffbc94584cc1904922d1c1fb",
              "validator_blob": blob, "head": subprocess.check_output(
                  ["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
              "cases": cases, "fixtures": all_rows}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("O217_DECISION=" + classification, flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--output", type=Path)
    p.add_argument("args", nargs="*")
    args = p.parse_args()
    if args.worker:
        if len(args.args) != 4: p.error("worker requires path logical_size mode repeats")
        worker(args.args[0], int(args.args[1]), args.args[2], int(args.args[3]))
    else:
        if args.args or args.output is None: p.error("need --output")
        controller(args.output)


if __name__ == "__main__":
    main()
