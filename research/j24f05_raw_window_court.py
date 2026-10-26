#!/usr/bin/env python3
"""J24F05: genuine revision-24 installed RAW transfer-window ownership court.

Research-level hostile source-writer control, separate from the stage-name pivot
(Issue #528). Success requires an unchanged authenticated output or fail-closed.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import tracemalloc

from j24f04_raw_chunk_immutable_transfer import (
    actor, blob_sha, independent_revision24, sha, trial as small_trial,
)

ROOT = Path(__file__).resolve().parents[1]
READER_BLOB = "41efeb9d3301fc06b1df56ab6bd42d9ee91f6d5e"
WINDOW = 64 * 1024
PYTHON_PEAK_BUDGET = 2 * 1024 * 1024  # extra tracked allocations, not whole RSS


def large_chunks():
    """Deterministic unrelated byte data; no external or private fixture identity."""
    return [
        hashlib.shake_256(b"J24F05 physical RAW large").digest(8 * 1024 * 1024),
        hashlib.shake_256(b"J24F05 physical RAW second").digest(131_072),
        hashlib.shake_256(b"J24F05 physical RAW third").digest(98_309),
    ]


def trial(directory: Path, storage_kind: int, mutate_future: bool):
    from cmpct.reader import CMPCT

    chunks = large_chunks()
    original = b"".join(chunks)
    name, packed, payload_offset = independent_revision24(chunks, storage_kind)
    flavor = "future-window" if mutate_future else "post-first-window"
    source = directory / f"large-source-{storage_kind}-{flavor}.cmpct"
    source.write_bytes(packed)
    del packed
    before = os.stat(source)
    before_sha = sha(source.read_bytes())

    # Mutate the first RAW window after it was already snapshotted OR a future
    # window in the SAME 8-MiB RAW physical chunk. The old whole-chunk candidate
    # may pass both, but must exceed the separate allocation budget.
    byte_position = (3 * WINDOW + 103) if mutate_future else 103
    attack_offset = payload_offset + byte_position
    original_fragment = chunks[0][byte_position:byte_position + 256]
    injected_fragment = bytes(x ^ 0xAD for x in original_fragment)

    with CMPCT(source) as reader:
        assert reader.read(name) == original
        assert reader.verify() == 1
        control = directory / f"control-{storage_kind}-{flavor}"
        reader.extractall(control, metadata=False)
        assert (control / name).read_bytes() == original

        destination = directory / f"out-{storage_kind}-{flavor}"
        destination.mkdir()
        sentinel = b"PRE-EXISTING SIGNED DESTINATION" if mutate_future else None
        if sentinel is not None:
            (destination / name).write_bytes(sentinel)

        real_write = os.write
        observations = []
        injected = []
        def intercepted(fd, payload):
            # This instrumentation wraps real stage write(2), never modifies the
            # Reader algorithm, a comparator, or the cryptographic expectation.
            length = len(payload)
            if length > WINDOW:
                raise AssertionError(f"RAW write exceeded immutable window: {length}")
            observations.append(length)
            if not injected:
                assert length == WINDOW and bytes(payload) == chunks[0][:WINDOW]
                st = os.fstat(fd)
                assert stat.S_ISREG(st.st_mode) and st.st_size == 0
                command = [
                    sys.executable, str(Path(__file__).resolve()), "--actor",
                    str(source), str(attack_offset),
                    base64.b64encode(injected_fragment).decode("ascii"),
                ]
                result = subprocess.run(
                    command, text=True, capture_output=True, timeout=15, check=True
                )
                evidence = json.loads(result.stdout)
                assert evidence["pid"] != os.getpid()
                assert evidence["altered_physical_payload_sha256"] == sha(injected_fragment)
                injected.append(evidence)
            return real_write(fd, payload)

        failure = None
        tracemalloc.start()
        try:
            tracemalloc.reset_peak()
            os.write = intercepted
            try:
                reader.extractall(destination, metadata=False)
            except Exception as exc:
                failure = repr(exc)
            finally:
                os.write = real_write
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
            os.write = real_write

    out_path = destination / name
    published = out_path.read_bytes() if out_path.exists() else None
    after = os.stat(source)
    same_source = (before.st_ino, before.st_dev, before.st_size) == (
        after.st_ino, after.st_dev, after.st_size)
    assert same_source and before_sha != sha(source.read_bytes())
    assert len(injected) == 1 and len(observations) > 120
    assert max(observations) <= WINDOW
    if mutate_future:
        safe = failure is not None and published == sentinel
    else:
        safe = failure is None and published == original
    if not safe:
        raise AssertionError(
            f"source write race violated authenticated output: {storage_kind}/{flavor}"
        )
    if peak > PYTHON_PEAK_BUDGET:
        raise AssertionError(f"Python allocation budget exceeded: {peak} B")

    return {
        "storage_kind": storage_kind,
        "case": flavor,
        "decision": "WINDOW_BOUND_TRANSFER_PASS",
        "actor": injected[0],
        "source_same_inode": same_source,
        "source_changed_sha": True,
        "whole_file_indexed_sha256": sha(original),
        "published_sha256": sha(published) if published is not None else None,
        "exception": failure,
        "logical_length": len(original),
        "max_stage_write_bytes": max(observations),
        "stage_write_calls": len(observations),
        "tracemalloc_peak_bytes": peak,
        "python_peak_budget_bytes": PYTHON_PEAK_BUDGET,
        "peak_kind": "Python traced heap only, not process RSS",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor", nargs=3)
    parser.add_argument("--output", default="j24f05.json")
    args = parser.parse_args()

    if args.actor:
        print(json.dumps(actor(args.actor[0], int(args.actor[1]), args.actor[2]),
                         sort_keys=True))
        return

    import cmpct.reader as mod
    installed = Path(mod.__file__).resolve()
    if installed.is_relative_to(ROOT):
        raise AssertionError("Reader not installed outside source checkout")
    actual_blob = blob_sha(installed.read_bytes())
    if actual_blob != READER_BLOB:
        raise AssertionError(("Reader blob is not the exact J24F05 candidate", actual_blob))

    with tempfile.TemporaryDirectory(prefix="j24f05-") as tempdir:
        temp = Path(tempdir)
        inherited = [small_trial(temp, kind, future)
                     for kind in (1, 5) for future in (False, True)]
        large = [trial(temp, kind, future)
                 for kind in (1, 5) for future in (False, True)]

    assert all(x["decision"] == "IMMUTABLE_TRANSFER_PASS" for x in inherited)
    assert all(x["decision"] == "WINDOW_BOUND_TRANSFER_PASS" for x in large)
    result = {
        "schema": "j24f05-r24-window-hostile-v1",
        "head_reader_blob": actual_blob,
        "installed_reader": str(installed),
        "platform": sys.platform,
        "inherited_small_cases": inherited,
        "new_large_cases": large,
        "outcome": "BOUNDED_WINDOW_CUSTODY_PASS",
        "nonclaims": ["whole-process RSS", "stage-name publication defense",
                      "Windows portability", "complete-product ABBA"],
    }
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True))
    print("J24F05_DECISION=BOUNDED_WINDOW_CUSTODY_PASS", flush=True)
    for case in large:
        print("J24F05_CASE=" + json.dumps(case, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
