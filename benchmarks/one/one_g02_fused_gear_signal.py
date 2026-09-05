"""ONE-G0.2 fused Gear-signal cost/value experiment.

This is a nomination-stage experiment, not a compressor. It compares a one-pass loop that
forms the existing fixed-chunk FNV signal with the same loop plus the exact inherited
CMPCT Gear signal. The Gear arm keeps only the first source position for each sparse
anchor hash and emits unverified source/target nominations; exact proof remains mandatory
before any Law can be emitted. The experiment isolates whether the signal itself can be
fused without a second source scan and whether it sees the one-byte-shift relationship.
"""
from __future__ import annotations

from hashlib import blake2b
import json
import os
import random
import statistics
import time
import zlib

REPETITIONS = 7
CHUNK = 64
ANCHOR_BITS = 10
ANCHOR_MASK = (1 << ANCHOR_BITS) - 1
MAX_GEAR_ENTRIES = 1 << 13
_FNV64_OFFSET = 0xCBF29CE484222325
_FNV64_PRIME = 0x100000001B3
_U64_MASK = (1 << 64) - 1


def _u64(data: bytes, *, person: bytes) -> int:
    return int.from_bytes(blake2b(data, digest_size=8, person=person[:16]).digest(), "little")


# Exact historical CMPCT resemblance Gear table derivation. Only the encoder-side
# content signal is inherited; no CDC chunk type or reader-visible mechanism is.
_GEAR = tuple(_u64(bytes([i]), person=b"cmpct-gear-v1") for i in range(256))


def _fixed_signal(data: bytes) -> dict[str, object]:
    fnv = _FNV64_OFFSET
    fingerprints = 0
    checksum = 0
    for position, value in enumerate(data):
        fnv ^= value
        fnv = (fnv * _FNV64_PRIME) & _U64_MASK
        if (position + 1) % CHUNK == 0:
            fingerprints += 1
            checksum ^= fnv
            fnv = _FNV64_OFFSET
    return {
        "fixed_fingerprints": fingerprints,
        "fixed_checksum": checksum,
        "gear_anchors": 0,
        "gear_entries": 0,
        "gear_nominations": (),
    }


def _fixed_plus_gear_signal(data: bytes) -> dict[str, object]:
    fnv = _FNV64_OFFSET
    gear = 0
    fingerprints = 0
    checksum = 0
    anchors = 0
    index: dict[int, int] = {}
    nominations: list[tuple[int, int]] = []
    for position, value in enumerate(data):
        fnv ^= value
        fnv = (fnv * _FNV64_PRIME) & _U64_MASK
        gear = ((gear << 1) + _GEAR[value]) & _U64_MASK
        if (position + 1) % CHUNK == 0:
            fingerprints += 1
            checksum ^= fnv
            fnv = _FNV64_OFFSET
        if position + 1 < CHUNK or gear & ANCHOR_MASK:
            continue
        anchors += 1
        start = position + 1 - CHUNK
        source = index.get(gear)
        if source is None:
            if len(index) < MAX_GEAR_ENTRIES:
                index[gear] = start
        else:
            nominations.append((source, start))
    return {
        "fixed_fingerprints": fingerprints,
        "fixed_checksum": checksum,
        "gear_anchors": anchors,
        "gear_entries": len(index),
        "gear_nominations": tuple(nominations),
    }


def _cases() -> dict[str, bytes]:
    basis = random.Random(13).randbytes(512 * 1024)
    return {
        "shifted_version_pair_1byte_insert": basis + b"X" + basis,
        "random_1mib": random.Random(11).randbytes(1024 * 1024),
        "zlib_random_payload": zlib.compress(random.Random(14).randbytes(1024 * 1024), level=9),
    }


def _median(fn) -> tuple[int, dict[str, object]]:
    samples: list[int] = []
    last: dict[str, object] | None = None
    for _ in range(REPETITIONS):
        t0 = time.perf_counter_ns()
        last = fn()
        samples.append(time.perf_counter_ns() - t0)
    assert last is not None
    return int(statistics.median(samples)), last


def run() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for name, data in _cases().items():
        base_ns, base = _median(lambda: _fixed_signal(data))
        gear_ns, candidate = _median(lambda: _fixed_plus_gear_signal(data))
        assert candidate["fixed_fingerprints"] == base["fixed_fingerprints"]
        assert candidate["fixed_checksum"] == base["fixed_checksum"]
        nominations = candidate["gear_nominations"]
        assert isinstance(nominations, tuple)
        exact_window_hits = sum(
            1 for source, target in nominations if data[source : source + CHUNK] == data[target : target + CHUNK]
        )
        rows.append({
            "case": name,
            "input_bytes": len(data),
            "source_scans_base": 1,
            "source_scans_with_gear": 1,
            "base_median_ns": base_ns,
            "fused_gear_median_ns": gear_ns,
            "fused_gear_elapsed_ratio_over_base": gear_ns / base_ns,
            "fixed_fingerprints": base["fixed_fingerprints"],
            "gear_anchors": candidate["gear_anchors"],
            "gear_entries": candidate["gear_entries"],
            "gear_nomination_count": len(nominations),
            "gear_exact_window_hits_for_oracle_review": exact_window_hits,
            "gear_false_window_nominations_for_oracle_review": len(nominations) - exact_window_hits,
        })
    return {
        "schema": "cmpct-one-g02-fused-gear-signal-v2",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "repetitions": REPETITIONS,
        "anchor_bits": ANCHOR_BITS,
        "signal_identity": "historical cmpct-gear-v1 table derivation",
        "claim_boundary": "nomination-stage one-pass signal experiment; exact-window checks are oracle review and nominations are never Laws",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
