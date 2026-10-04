from __future__ import annotations

"""Resource-bounded streaming-parser hostile review for the compact monotone locator.

Mission Lock / Referee
======================
v3 bounds compressed-locator expansion before allocation but still inherits v1's `_parse_locator`,
which materializes a Python dict of lists of `(key, offset)` tuples. A syntactically valid hostile
locator near the 1 MiB raw ceiling can therefore amplify one bounded byte buffer into a much larger
object graph. That is parser-state debt, not a density/locality tradeoff.

The frozen representation is unchanged: same LOC1 bytes, zlib-9 body, 644 B groups, primary/tail
frames, footer/root, corpus, same-input v0.29 comparator and 8x locality law.

Hypothesis
----------
Because LOC1 is canonical and monotone, the reader needs no retained per-record table. Validate the
entire locator in one streaming O(raw-bytes) pass, retain only the already-bounded raw bytes, and expose
re-iterable family views whose iteration rescans those bytes. The complete inherited v3 referee must
produce identical density/locality economics and exact recovery while malformed/non-canonical input
fails closed.

Disproof
--------
False if any inherited result changes, exact records cannot be recovered, the streaming parser retains
state proportional to record count beyond the bounded raw buffer, non-canonical uvarints are accepted,
stream order/duplication is accepted, or a near-ceiling valid locator cannot be validated with constant
retained parser state. No representation bytes, thresholds, codec level, admission or 8x limit move.

PASS remains diagnostic only; canonical r25 integration, product trust-anchor binding, isolated
CPU/RSS/read-throughput, held-out transfer, native/platform parity and broader malformed-input fuzzing
remain promotion debt.
"""

import argparse
import json
import os
from pathlib import Path
import sys

from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_office_compact_monotone_directory_referee as V1
from benchmarks import v030_r4_office_compact_monotone_directory_v3 as V3

SCHEMA = "cmpct-v030-r4-office-compact-monotone-directory-v4"
MAX_LOCATOR_RAW = V3.MAX_LOCATOR_RAW


def _read_canonical_uvarint(buf: bytes, off: int) -> tuple[int, int]:
    start = off
    value, off = V1._read_uvarint(buf, off)
    if bytes(buf[start:off]) != DEP.uvarint(value):
        raise ValueError("non-canonical locator uvarint")
    return value, off


def _validate_locator(raw: bytes) -> tuple[int, int]:
    if len(raw) > MAX_LOCATOR_RAW:
        raise RuntimeError("locator expansion bound exceeded")
    if not raw.startswith(b"LOC1"):
        raise ValueError("bad locator magic")
    off = 4
    stream_count, off = _read_canonical_uvarint(raw, off)
    prev_si = -1
    records = 0
    for _ in range(stream_count):
        si, off = _read_canonical_uvarint(raw, off)
        if si <= prev_si:
            raise ValueError("locator stream order/duplication")
        prev_si = si
        for expected_fam in V1.FAMS:
            fid, off = _read_canonical_uvarint(raw, off)
            if fid != V1.FAM_ID[expected_fam]:
                raise ValueError("locator family order drift")
            count, off = _read_canonical_uvarint(raw, off)
            key = 0
            roff = 0
            for _j in range(count):
                dk, off = _read_canonical_uvarint(raw, off)
                do, off = _read_canonical_uvarint(raw, off)
                key += dk
                roff += do
                records += 1
    if off != len(raw):
        raise ValueError("trailing locator bytes")
    return stream_count, records


def _iter_family(raw: bytes, target_si: int, target_fam: str):
    off = 4
    stream_count, off = _read_canonical_uvarint(raw, off)
    for _ in range(stream_count):
        si, off = _read_canonical_uvarint(raw, off)
        for expected_fam in V1.FAMS:
            fid, off = _read_canonical_uvarint(raw, off)
            if fid != V1.FAM_ID[expected_fam]:
                raise ValueError("locator family order drift")
            count, off = _read_canonical_uvarint(raw, off)
            key = 0
            roff = 0
            match = si == target_si and expected_fam == target_fam
            for _j in range(count):
                dk, off = _read_canonical_uvarint(raw, off)
                do, off = _read_canonical_uvarint(raw, off)
                key += dk
                roff += do
                if match:
                    yield (key, roff)
    if off != len(raw):
        raise ValueError("trailing locator bytes")


class _FamilyRows:
    __slots__ = ("_raw", "_si", "_fam")

    def __init__(self, raw: bytes, si: int, fam: str):
        self._raw = raw
        self._si = si
        self._fam = fam

    def __iter__(self):
        return _iter_family(self._raw, self._si, self._fam)


class _LocatorView:
    __slots__ = ("_raw", "stream_count", "record_count")

    def __init__(self, raw: bytes):
        self.stream_count, self.record_count = _validate_locator(raw)
        self._raw = raw

    def __getitem__(self, sf: tuple[int, str]):
        si, fam = sf
        if fam not in V1.FAMS:
            raise KeyError(sf)
        return _FamilyRows(self._raw, int(si), fam)


def _parse_locator_streaming(raw: bytes) -> _LocatorView:
    return _LocatorView(raw)


def _large_valid_locator(target_bytes: int = 900_000) -> bytes:
    # One stream, one dense family of zero deltas; every row costs exactly two canonical bytes.
    # The other two required families remain empty. Build below the 1 MiB raw ceiling so this attacks
    # parser object amplification rather than the already-covered decompression ceiling.
    fixed = bytearray(b"LOC1")
    fixed += DEP.uvarint(1)      # stream count
    fixed += DEP.uvarint(0)      # stream id
    # Determine a count whose encoded body stays below target_bytes; no sweep of product parameters is
    # involved -- this is hostile-input construction only.
    count = max(1, (target_bytes - 32) // 2)
    while True:
        raw = bytearray(fixed)
        raw += DEP.uvarint(V1.FAM_ID["anchor"]) + DEP.uvarint(count)
        raw += b"\x00\x00" * count
        raw += DEP.uvarint(V1.FAM_ID["block"]) + DEP.uvarint(0)
        raw += DEP.uvarint(V1.FAM_ID["seed"]) + DEP.uvarint(0)
        if len(raw) <= target_bytes:
            return bytes(raw)
        count -= 1


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    original_parse = V1._parse_locator
    V1._parse_locator = _parse_locator_streaming
    try:
        d = V3.run(work, v029_checkout, worker)
    finally:
        V1._parse_locator = original_parse

    hostile = _large_valid_locator()
    view = _parse_locator_streaming(hostile)
    # The retained parser object is constant-size and contains only one reference to the already-bounded
    # raw buffer plus scalar counters. It contains no dict/list/tuple table proportional to record count.
    retained_parser_bytes = sys.getsizeof(view)
    constant_state_shape = (
        not hasattr(view, "__dict__")
        and view.record_count > 100_000
        and retained_parser_bytes < 1024
        and len(hostile) <= MAX_LOCATOR_RAW
    )

    # Canonical-encoding hostile control: overlong zero is semantically 0 but must not have a second
    # accepted byte spelling. Start from the minimum empty locator grammar.
    noncanonical = b"LOC1\x81\x00"  # stream_count=1, deliberately overlong; remaining bytes unnecessary
    noncanonical_rejected = False
    try:
        _parse_locator_streaming(noncanonical)
    except ValueError as exc:
        noncanonical_rejected = "non-canonical" in str(exc)

    # Duplicate/out-of-order stream ids are invalid even when every family is empty.
    dup = bytearray(b"LOC1") + DEP.uvarint(2)
    for _ in range(2):
        dup += DEP.uvarint(0)
        for fam in V1.FAMS:
            dup += DEP.uvarint(V1.FAM_ID[fam]) + DEP.uvarint(0)
    duplicate_stream_rejected = False
    try:
        _parse_locator_streaming(bytes(dup))
    except ValueError as exc:
        duplicate_stream_rejected = "stream order" in str(exc)

    prior = bool(d["hypothesis"]["compact_monotone_locator_preserves_density_8x_integrity_and_resource_bound"])
    parser_ok = constant_state_shape and noncanonical_rejected and duplicate_stream_rejected
    d["schema"] = SCHEMA
    d["source_commit"] = os.environ.get("EVIDENCE_HEAD")
    d["hostile_controls"].update({
        "near_ceiling_locator_uses_constant_retained_parser_state": constant_state_shape,
        "noncanonical_uvarint_rejected": noncanonical_rejected,
        "duplicate_or_nonmonotone_stream_id_rejected": duplicate_stream_rejected,
    })
    d["resource_bounds"].update({
        "streaming_parser": True,
        "retained_record_table": False,
        "hostile_valid_locator_bytes": len(hostile),
        "hostile_valid_locator_records": view.record_count,
        "retained_parser_object_bytes_excluding_raw_buffer": retained_parser_bytes,
    })
    d["contract"]["v3_non_authoritative_after_parser_state_hostile_review"] = True
    d["contract"]["canonical_uvarints_required"] = True
    d["contract"]["monotone_unique_stream_ids_required"] = True
    d["hypothesis"] = {
        "compact_monotone_locator_preserves_density_8x_integrity_and_bounded_parser_state": prior and parser_ok,
    }
    return d


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory-v4-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory-v4.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "compact_locator": d["compact_locator"],
        "selective_read": d["selective_read"],
        "hostile_controls": d["hostile_controls"],
        "resource_bounds": d["resource_bounds"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
