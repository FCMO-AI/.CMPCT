from __future__ import annotations

"""Hostile-review v5: separate compressed-input and raw-output locator ceilings.

v3/v4 correctly bounded locator expansion, but compared the compressed body length to the raw
1 MiB ceiling. DEFLATE can expand incompressible input slightly, so that check could reject an
otherwise raw-bounded frame. The representation and every economic/locality parameter remain frozen.

Hypothesis: using zlib's deterministic compressBound formula for the compressed-input ceiling while
retaining the 1 MiB raw-output ceiling preserves every v4 result, accepts bounded-but-incompressible
frame payloads at the frame layer, and still rejects oversized compressed input before allocation.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import zlib

from benchmarks import v030_r4_office_compact_monotone_directory_referee as V1
from benchmarks import v030_r4_office_compact_monotone_directory_v3 as V3
from benchmarks import v030_r4_office_compact_monotone_directory_v4 as V4

SCHEMA = "cmpct-v030-r4-office-compact-monotone-directory-v5"
MAX_LOCATOR_RAW = V3.MAX_LOCATOR_RAW
MAX_LOCATOR_BODY = (
    MAX_LOCATOR_RAW
    + (MAX_LOCATOR_RAW >> 12)
    + (MAX_LOCATOR_RAW >> 14)
    + (MAX_LOCATOR_RAW >> 25)
    + 13
)


def _read_frame_dual_bound(fd: int, off: int) -> tuple[bytes, int, bytes]:
    head = V1.SER._read_exact(fd, V1.HDR.size, off)
    magic, _si, _fam, _count, body_len, group_base, digest = V1.HDR.unpack(head)
    if magic != b"LOC1" or body_len > MAX_LOCATOR_BODY:
        raise RuntimeError("malformed compact locator header")
    body = V1.SER._read_exact(fd, body_len, off + V1.HDR.size)
    if hashlib.sha256(body).digest() != digest:
        raise ValueError("locator digest mismatch")
    dec = zlib.decompressobj()
    try:
        raw = dec.decompress(body, MAX_LOCATOR_RAW + 1)
    except zlib.error as exc:
        raise ValueError("locator decompression failed") from exc
    if len(raw) > MAX_LOCATOR_RAW or not dec.eof or dec.unconsumed_tail:
        raise RuntimeError("locator expansion bound exceeded")
    if dec.unused_data:
        raise ValueError("trailing compressed locator stream")
    return raw, group_base, head + body


def _write_frame(path: Path, raw: bytes) -> int:
    body = zlib.compress(raw, 9)
    head = V1.HDR.pack(b"LOC1", 0, 0, 0, len(body), 0, hashlib.sha256(body).digest())
    path.write_bytes(head + body)
    return len(body)


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)

    original = V3._read_frame_bounded
    V3._read_frame_bounded = _read_frame_dual_bound
    try:
        d = V4.run(work, v029_checkout, worker)
    finally:
        V3._read_frame_bounded = original

    # Frame-layer representability control. The raw bytes intentionally need not be a valid locator:
    # grammar validation is the next layer. This isolates the body-length ceiling from parser policy.
    incompressible = work / "locator-incompressible-frame.bin"
    raw = os.urandom(MAX_LOCATOR_RAW)
    body_len = _write_frame(incompressible, raw)
    fd = os.open(incompressible, os.O_RDONLY)
    try:
        bounded_expanded_body_accepted = False
        try:
            got, _base, _charged = _read_frame_dual_bound(fd, 0)
            bounded_expanded_body_accepted = got == raw and body_len > MAX_LOCATOR_RAW
        except Exception:
            bounded_expanded_body_accepted = False
    finally:
        os.close(fd)

    # Oversized compressed input must fail from the header alone, before reading attacker-selected bytes.
    oversized = work / "locator-oversized-body-header.bin"
    fake_digest = b"\x00" * 32
    oversized.write_bytes(V1.HDR.pack(b"LOC1", 0, 0, 0, MAX_LOCATOR_BODY + 1, 0, fake_digest))
    fd = os.open(oversized, os.O_RDONLY)
    try:
        oversized_body_rejected = False
        try:
            _read_frame_dual_bound(fd, 0)
        except RuntimeError as exc:
            oversized_body_rejected = "malformed compact locator header" in str(exc)
    finally:
        os.close(fd)

    prior = bool(d["hypothesis"]["compact_monotone_locator_preserves_density_8x_integrity_and_bounded_parser_state"])
    bound_ok = bounded_expanded_body_accepted and oversized_body_rejected
    d["schema"] = SCHEMA
    d["source_commit"] = os.environ.get("EVIDENCE_HEAD")
    d["hostile_controls"].update({
        "raw_bounded_incompressible_frame_body_above_raw_ceiling_accepted": bounded_expanded_body_accepted,
        "compressed_body_above_compress_bound_rejected_from_header": oversized_body_rejected,
    })
    d["resource_bounds"].update({
        "max_locator_raw_bytes": MAX_LOCATOR_RAW,
        "max_locator_compressed_body_bytes": MAX_LOCATOR_BODY,
        "compressed_and_raw_bounds_are_distinct": True,
    })
    d["contract"]["v4_non_authoritative_after_compressed_bound_hostile_review"] = True
    d["contract"]["zlib_compress_bound_formula"] = "n+(n>>12)+(n>>14)+(n>>25)+13"
    d["hypothesis"] = {
        "compact_monotone_locator_preserves_density_8x_integrity_parser_and_frame_bounds": prior and bound_ok,
    }
    return d


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory-v5-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory-v5.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"compact_locator":d["compact_locator"],"selective_read":d["selective_read"],"hostile_controls":d["hostile_controls"],"resource_bounds":d["resource_bounds"],"hypothesis":d["hypothesis"]},sort_keys=True))


if __name__ == "__main__":
    main()
