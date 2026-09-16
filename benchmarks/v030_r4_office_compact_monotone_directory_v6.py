from __future__ import annotations

"""Deterministic hostile-review v6 for compact monotone locator frame bounds.

v5 separated compressed-input and raw-output ceilings correctly, but its incompressible frame control
used ``os.urandom``. That makes a benchmark receipt probabilistic even though the product mechanism is
unchanged. v6 freezes the hostile payload with a fixed PRNG seed and re-runs the complete v4 referee
under the same dual-bound reader.

Hypothesis: a deterministic 1 MiB high-entropy payload produces a zlib body above the raw ceiling but
at or below zlib's compressBound, is accepted at the frame layer, while MAX_BODY+1 is rejected from
the header. All inherited density/locality/integrity/parser results must remain unchanged.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import zlib

from benchmarks import v030_r4_office_compact_monotone_directory_referee as V1
from benchmarks import v030_r4_office_compact_monotone_directory_v3 as V3
from benchmarks import v030_r4_office_compact_monotone_directory_v4 as V4
from benchmarks import v030_r4_office_compact_monotone_directory_v5 as V5

SCHEMA = "cmpct-v030-r4-office-compact-monotone-directory-v6"
MAX_LOCATOR_RAW = V5.MAX_LOCATOR_RAW
MAX_LOCATOR_BODY = V5.MAX_LOCATOR_BODY
HOSTILE_SEED = 0xC030A6E


def _read_frame_dual_bound(fd: int, off: int) -> tuple[bytes, int, bytes]:
    return V5._read_frame_dual_bound(fd, off)


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

    incompressible = work / "locator-deterministic-incompressible-frame.bin"
    raw = random.Random(HOSTILE_SEED).randbytes(MAX_LOCATOR_RAW)
    body_len = _write_frame(incompressible, raw)
    fd = os.open(incompressible, os.O_RDONLY)
    try:
        bounded_expanded_body_accepted = False
        try:
            got, _base, _charged = _read_frame_dual_bound(fd, 0)
            bounded_expanded_body_accepted = (
                got == raw
                and MAX_LOCATOR_RAW < body_len <= MAX_LOCATOR_BODY
            )
        except Exception:
            bounded_expanded_body_accepted = False
    finally:
        os.close(fd)

    oversized = work / "locator-oversized-body-header.bin"
    oversized.write_bytes(V1.HDR.pack(b"LOC1", 0, 0, 0, MAX_LOCATOR_BODY + 1, 0, b"\x00" * 32))
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
        "deterministic_raw_bounded_incompressible_frame_body_above_raw_ceiling_accepted": bounded_expanded_body_accepted,
        "compressed_body_above_compress_bound_rejected_from_header": oversized_body_rejected,
    })
    d["resource_bounds"].update({
        "max_locator_raw_bytes": MAX_LOCATOR_RAW,
        "max_locator_compressed_body_bytes": MAX_LOCATOR_BODY,
        "compressed_and_raw_bounds_are_distinct": True,
        "deterministic_hostile_seed": HOSTILE_SEED,
        "deterministic_hostile_compressed_body_bytes": body_len,
    })
    d["contract"]["v5_non_authoritative_due_nondeterministic_hostile_control"] = True
    d["contract"]["zlib_compress_bound_formula"] = "n+(n>>12)+(n>>14)+(n>>25)+13"
    d["hypothesis"] = {
        "compact_monotone_locator_preserves_density_8x_integrity_parser_and_dual_bounds": prior and bound_ok,
    }
    return d


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory-v6-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory-v6.json"))
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
