#!/usr/bin/env python3
"""J24G10: real installed CMPCT Reader, exact parent, and unbounded-set oracle.

Scientific evaluation only. Generates genuine Builder/Writer archives, appends
SHA-authenticated orphan deltas, and measures actual code rather than simulated
footer selection. Same physical archive bytes for all three Readers.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import resource
import statistics
import subprocess
import tempfile
import time
import tracemalloc
import types
from pathlib import Path
from unittest.mock import patch

import msgpack
import cmpct.reader as product
from cmpct.builder import Builder
from cmpct.codec import FTR, FMAGIC, sha
from cmpct.transactions import append_rename
from j24g09_invalid_ancestry_ap_court import PAYLOAD, digest, orphan_tail, variant_orphan_tail

PARENT = "11963e53947829ce141e9910fdd4adf0d866fb5f"
PARENT_BLOB = "ec0335268d0486e41b460f14b1a3543b7cb1a589"
CANDIDATE_BLOB = "690ab86564c9f2989ed4af0879167d8394140dd0"
N = 16400
REPEATS = 3


def old_reader():
    got = subprocess.check_output(
        ["git", "rev-parse", PARENT + ":src/cmpct/reader.py"], text=True
    ).strip()
    assert got == PARENT_BLOB, got
    raw = subprocess.check_output(["git", "show", PARENT + ":src/cmpct/reader.py"])
    module = types.ModuleType("cmpct._j24g10_exact_parent")
    module.__package__ = "cmpct"
    exec(compile(raw, "<actual Git parent Reader>", "exec"), module.__dict__)
    return module.CMPCT


class UnboundedExactProof:
    """Strong simpler *oracle*: exact Python set, unbounded resident memory."""
    def __init__(self):
        self.positions = set()

    def __contains__(self, key):
        return key in self.positions

    def __len__(self):
        return len(self.positions)

    def update(self, keys):
        self.positions.update(keys)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return None


def unbounded_oracle_reader():
    raw = subprocess.check_output(["git", "show", "HEAD:src/cmpct/reader.py"])
    assert subprocess.check_output(
        ["git", "rev-parse", "HEAD:src/cmpct/reader.py"], text=True
    ).strip() == CANDIDATE_BLOB
    module = types.ModuleType("cmpct._j24g10_unbounded_oracle")
    module.__package__ = "cmpct"
    exec(compile(raw, "<exact HEAD Reader with research proof-store substitution>", "exec"),
         module.__dict__)
    # Only substitute the proof-store object, never the parser or recovery logic.
    module._FooterInvalidProof = UnboundedExactProof
    return module.CMPCT


def arbitrary_tail(base: bytes, n: int, seed: int) -> bytes:
    rng = random.Random(seed)
    raw = bytearray(base)
    prev = 0
    for i in range(n):
        width = rng.randrange(13)
        payload = msgpack.packb({"blobs": [], "ops": [], "pad": b"Q" * width},
                                use_bin_type=True)
        pos = len(raw) + len(payload)
        raw.extend(payload)
        raw.extend(FTR.pack(FMAGIC, 1, 0, 0, 0, len(payload), len(payload),
                            prev, sha(payload)))
        prev = pos
    return bytes(raw)


def oracle_exact_membership():
    cls = product._FooterInvalidProof
    rng = random.Random(0xF00DCAFE)
    keys = set(rng.randrange(1, 1 << 40) for _ in range(30000))
    keys.update((0, 1, (1 << 63) - 1, 1 << 63, (1 << 64) - 1))
    probes = set(keys)
    for key in list(sorted(keys))[:15000]:
        probes.add((key + 2) % (1 << 64))
    with cls() as store:
        store.update(keys)
        assert len(store) == len(keys)
        assert all(x in store for x in keys)
        assert all((x in store) == (x in keys) for x in probes)
        path = store._path
        assert path and os.path.isfile(path)
        db_bytes = os.path.getsize(path)
        assert db_bytes <= 32 * len(keys), (db_bytes, len(keys))
        assert not store.hot
        store.update({1 << 63, (1 << 64) - 1, 0, 42})
        assert 42 in store
        assert len(store) == len(keys | {42})
    assert not os.path.exists(path), "transient proof file leaked after normal close"
    # An insert failure must be terminal rather than a false set membership.
    try:
        with cls() as store:
            store.update(keys)
            store.update({1 << 64})
    except ValueError:
        pass
    else:
        raise AssertionError("unsigned uint64 overflow silently admitted")
    return {"exact_positive": len(keys), "probe_count": len(probes),
            "db_bytes": db_bytes, "temp_removed": True,
            "high_u64_offsets": True, "overflow_fail_closed": True}


def measure(cls, archive: Path, checkpoint: int, target: str = "owner.bin") -> dict:
    dec = cls._decode_generation_payload
    decodes = 0
    spills = []

    def wrapped(self, pos):
        nonlocal decodes
        decodes += 1
        return dec(self, pos)

    close_orig = product._FooterInvalidProof.close

    def watched_close(self):
        if self._path and os.path.isfile(self._path):
            spills.append(os.path.getsize(self._path))
        return close_orig(self)

    started = time.perf_counter_ns()
    cpu = time.process_time_ns()
    with patch.object(cls, "_decode_generation_payload", wrapped):
        if cls is product.CMPCT:
            # Audit the physical spill before the actual Reader removes it.
            with patch.object(product._FooterInvalidProof, "close", watched_close):
                with cls(archive) as ar:
                    check_archive(ar, checkpoint, target)
        else:
            with cls(archive) as ar:
                check_archive(ar, checkpoint, target)
    return {"decoder_calls": decodes, "wall_ms": (time.perf_counter_ns()-started)/1e6,
            "cpu_ms": (time.process_time_ns()-cpu)/1e6,
            "spill_bytes": spills, "physical_bytes": archive.stat().st_size}


def check_archive(ar, checkpoint, target):
    assert ar.latest_footer_pos == checkpoint
    assert ar.read(target) == PAYLOAD
    assert ar.read_range(target, 0, 19) == PAYLOAD[:19]
    assert ar.read_range(target, len(PAYLOAD)-23, 23) == PAYLOAD[-23:]
    ar.verify()


def paired(Historical, Oracle, path, checkpoint, expected_old, expected_new,
           label, target="owner.bin", repeats=REPEATS):
    classes = {"parent": Historical, "candidate": product.CMPCT, "unbounded": Oracle}
    rows = {k: [] for k in classes}
    for rep in range(repeats):
        ordering = list(classes) if rep % 2 == 0 else list(reversed(classes))
        for name in ordering:
            rows[name].append(measure(classes[name], path, checkpoint, target))
    for x in rows["parent"]:
        assert x["decoder_calls"] == expected_old, (label, x)
    for name in ("candidate", "unbounded"):
        for x in rows[name]:
            assert x["decoder_calls"] == expected_new, (label, name, x)
    out = {"case": label, "archive_sha256": digest(path.read_bytes()),
           "archive_bytes": path.stat().st_size, "rows": rows,
           "median_wall_ms": {k: statistics.median(r["wall_ms"] for r in v)
                              for k, v in rows.items()},
           "median_cpu_ms": {k: statistics.median(r["cpu_ms"] for r in v)
                             for k, v in rows.items()}}
    print("J24G10_CASE=" + json.dumps(out, sort_keys=True), flush=True)
    return out


def main():
    assert subprocess.check_output(
        ["git", "rev-parse", "HEAD:src/cmpct/reader.py"], text=True
    ).strip() == CANDIDATE_BLOB
    path = Path(product.__file__).resolve()
    assert "site-packages" in str(path), path
    assert path.read_bytes() == subprocess.check_output(
        ["git", "show", "HEAD:src/cmpct/reader.py"]), path
    Historical = old_reader()
    Oracle = unbounded_oracle_reader()
    membership = oracle_exact_membership()
    output = Path(os.environ.get("J24G10_ARTIFACTS", "j24g10-artifacts"))
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g10-") as td:
        root = Path(td)
        tree = root / "tree"
        tree.mkdir()
        (tree / "owner.bin").write_bytes(PAYLOAD)
        pristine = root / "pristine.cmpct"
        Builder(tree).build(pristine)
        base = pristine.read_bytes()
        with product.CMPCT(pristine) as ar:
            checkpoint = ar.latest_footer_pos
            assert checkpoint > 0 and ar.read("owner.bin") == PAYLOAD
        cases = {}
        def record(label, data, expected_old, expected_new, repeats=REPEATS):
            p = root / (label + ".cmpct")
            p.write_bytes(data)
            cases[label] = paired(Historical, Oracle, p, checkpoint, expected_old,
                                  expected_new, label, repeats=repeats)

        record("alternating-16400", variant_orphan_tail(base, N, "alternating"),
               278665, N+1)
        record("random-16400", arbitrary_tail(base, N, seed=20261028),
               278665, N+1)
        record("uniform-ap-16400", orphan_tail(base, N, True),
               N+1, N+1)
        record("flat-1024", orphan_tail(base, 1024, False),
               1025, 1025, repeats=3)
        baseline = root / "valid-rename.cmpct"
        baseline.write_bytes(base)
        append_rename(baseline, "owner.bin", "renamed.bin")
        with product.CMPCT(baseline) as ar:
            valid_footer = ar.latest_footer_pos
            assert valid_footer > checkpoint
        valid = paired(Historical, Oracle, baseline, valid_footer, 2, 2,
                       "valid-first-party-rename", target="renamed.bin")
        cases["valid-first-party-rename"] = valid

        for label in ("alternating-16400", "random-16400"):
            test = cases[label]
            assert all(m["spill_bytes"] for m in test["rows"]["candidate"])
            assert all(m["spill_bytes"][0] <= 32 * N
                       for m in test["rows"]["candidate"])
            assert test["median_wall_ms"]["parent"] / test["median_wall_ms"]["candidate"] >= 5.0
        for label in ("uniform-ap-16400", "flat-1024", "valid-first-party-rename"):
            test = cases[label]
            assert all(not m["spill_bytes"] for m in test["rows"]["candidate"])
            assert test["median_wall_ms"]["candidate"] <= 1.25 * test["median_wall_ms"]["parent"], label
        result = {
            "status": "RESEARCH_BOUND_CROSS_CANDIDATE_STORE_ONLY",
            "parent_head": PARENT, "parent_reader_blob": PARENT_BLOB,
            "candidate_reader_blob": CANDIDATE_BLOB,
            "builder_archive_bytes": len(base), "builder_archive_sha256": digest(base),
            "logical_sha256": digest(PAYLOAD), "membership_oracle": membership,
            "cases": cases, "repeats": REPEATS,
            "full_RSS_bounded": False,
            "per_chain_seen_chain_bounded": False,
            "mutable_source_supported": False,
            "release_credit": 0
        }
        (output / "court.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
        print("J24G10_RESULT=" + json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
