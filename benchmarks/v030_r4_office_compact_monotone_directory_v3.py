from __future__ import annotations

"""Resource-bounded hostile-review v3 for the compact monotone Office locator.

Mission Lock / Referee
======================
The v2 representation, bytes, 644 B authenticated groups, economics, locality limit, corpus,
and frozen-v0.29 comparison remain unchanged. Hostile review found one parser/resource defect in
the experimental locator reader: v1/v2 called ``zlib.decompress(body)`` and only then checked that
the expanded locator was <= 1 MiB. A tiny hostile body could therefore allocate far beyond the
claimed reader ceiling before rejection.

Hypothesis
----------
The exact same compact-locator representation can be read with a hard pre-allocation expansion
ceiling by using ``zlib.decompressobj().decompress(..., MAX+1)`` and failing closed unless the
stream reaches EOF with <= MAX bytes and no trailing compressed stream. The resulting reader must
preserve every v2 byte/economic/locality result and hostile integrity result.

Disproof
--------
The mechanism is false if the bounded reader changes any stored-byte/locality economics, cannot
recover every existing record exactly, accepts a locator that expands beyond 1 MiB, accepts a
concatenated/trailing compressed locator stream, or weakens any v2 corruption/recovery control.
No density/locality threshold, group geometry, codec level or workload admission may change.

A PASS remains diagnostic only. Canonical r25 integration, real product archive-root binding,
process-isolated CPU/RSS, held-out transfer, malformed-locator fuzz breadth and native/platform
parity remain promotion debt.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import zlib

from benchmarks import v030_r4_office_compact_monotone_directory_referee as V1
from benchmarks import v030_r4_office_compact_monotone_directory_v2 as V2

SCHEMA = "cmpct-v030-r4-office-compact-monotone-directory-v3"
MAX_LOCATOR_RAW = 1_048_576


def _read_frame_bounded(fd: int, off: int) -> tuple[bytes, int, bytes]:
    head = V1.SER._read_exact(fd, V1.HDR.size, off)
    magic, _si, _fam, _count, body_len, group_base, digest = V1.HDR.unpack(head)
    if magic != b"LOC1" or body_len > MAX_LOCATOR_RAW:
        raise RuntimeError("malformed compact locator header")
    body = V1.SER._read_exact(fd, body_len, off + V1.HDR.size)
    if hashlib.sha256(body).digest() != digest:
        raise ValueError("locator digest mismatch")

    dec = zlib.decompressobj()
    try:
        raw = dec.decompress(body, MAX_LOCATOR_RAW + 1)
    except zlib.error as exc:
        raise ValueError("locator decompression failed") from exc
    # Crucially, reject before requesting any more output. ``MAX+1`` makes an over-limit stream
    # observable while bounding this Python allocation independently of the attacker's expansion.
    if len(raw) > MAX_LOCATOR_RAW or not dec.eof or dec.unconsumed_tail:
        raise RuntimeError("locator expansion bound exceeded")
    if dec.unused_data:
        raise ValueError("trailing compressed locator stream")
    return raw, group_base, head + body


def _hostile_frame(path: Path, raw: bytes, *, suffix: bytes = b"") -> None:
    body = zlib.compress(raw, 9) + suffix
    head = V1.HDR.pack(b"LOC1", 0, 0, 0, len(body), 0, hashlib.sha256(body).digest())
    path.write_bytes(head + body)


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)

    # Exercise the complete inherited v2 referee through the bounded reader, not merely a side test.
    original = V1._read_frame
    V1._read_frame = _read_frame_bounded
    try:
        d = V2.run(work, v029_checkout, worker)
    finally:
        V1._read_frame = original

    bomb = work / "compact-monotone-expansion-bomb.bin"
    _hostile_frame(bomb, b"A" * (MAX_LOCATOR_RAW + 1))
    fd = os.open(bomb, os.O_RDONLY)
    try:
        expansion_bomb_rejected = False
        try:
            _read_frame_bounded(fd, 0)
        except RuntimeError as exc:
            expansion_bomb_rejected = "expansion bound" in str(exc)
    finally:
        os.close(fd)

    trailing = work / "compact-monotone-trailing-stream.bin"
    first = zlib.compress(b"LOC1" + b"\x00", 9)
    second = zlib.compress(b"ignored", 9)
    body = first + second
    trailing.write_bytes(
        V1.HDR.pack(b"LOC1", 0, 0, 0, len(body), 0, hashlib.sha256(body).digest()) + body
    )
    fd = os.open(trailing, os.O_RDONLY)
    try:
        trailing_stream_rejected = False
        try:
            _read_frame_bounded(fd, 0)
        except ValueError as exc:
            trailing_stream_rejected = "trailing compressed" in str(exc)
    finally:
        os.close(fd)

    prior = bool(d["hypothesis"]["compact_monotone_locator_preserves_density_8x_and_root_fail_closed"])
    resource_ok = expansion_bomb_rejected and trailing_stream_rejected
    d["schema"] = SCHEMA
    d["source_commit"] = os.environ.get("EVIDENCE_HEAD")
    d["hostile_controls"].update({
        "over_limit_locator_expansion_rejected_before_unbounded_output": expansion_bomb_rejected,
        "concatenated_trailing_locator_stream_rejected": trailing_stream_rejected,
    })
    d["resource_bounds"] = {
        "max_locator_raw_bytes": MAX_LOCATOR_RAW,
        "bounded_output_request_bytes": MAX_LOCATOR_RAW + 1,
        "unbounded_zlib_decompress_removed_from_authoritative_reader": True,
    }
    d["hypothesis"] = {
        "compact_monotone_locator_preserves_density_8x_integrity_and_resource_bound": prior and resource_ok,
    }
    d["contract"]["v2_non_authoritative_after_resource_hostile_review"] = True
    d["contract"]["locator_expansion_must_be_bounded_before_full_materialization"] = True
    return d


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory-v3-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory-v3.json"))
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
