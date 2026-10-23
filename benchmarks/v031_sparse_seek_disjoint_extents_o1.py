#!/usr/bin/env python3
"""Independent regression court: source-exact SEEK_DATA extent boundaries.

Scientific-only: preserves PR296 oracle and PR293 product scanner unchanged.
Original O1 phantom hypothesis was FALSIFIED by hosted source-exact evidence.
This successor court preserves its three layouts as held-out parity controls.
"""
from __future__ import annotations

import binascii
import errno
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v031_sparse_seek_salvage_court import sparse_candidates
from cmpct.codec import BHDR, BMAGIC, CODEC_RAW
from cmpct.transactions import recover_blob_records

_A = 4096
_B = 2 << 20
_C = 4 << 20
_SIZE = 8 << 20
_UNSUPPORTED = {getattr(errno, x) for x in ("EINVAL", "ENOTSUP", "EOPNOTSUPP", "ENOSYS") if hasattr(errno, x)}


def _extents(path: Path) -> list[tuple[int, int]]:
    fd = os.open(path, os.O_RDONLY)
    try:
        size = os.fstat(fd).st_size
        if not (hasattr(os, "SEEK_DATA") and hasattr(os, "SEEK_HOLE")):
            raise RuntimeError("UNSUPPORTED: missing SEEK_DATA/SEEK_HOLE")
        cursor, out = 0, []
        while cursor < size:
            try:
                start = os.lseek(fd, cursor, os.SEEK_DATA)
            except OSError as exc:
                if exc.errno == errno.ENXIO:
                    break
                if exc.errno in _UNSUPPORTED:
                    raise RuntimeError("UNSUPPORTED: incoherent/unsupported SEEK_DATA") from exc
                raise
            stop = os.lseek(fd, start, os.SEEK_HOLE)
            if not cursor <= start < stop <= size:
                raise RuntimeError("UNSUPPORTED: incoherent extent boundaries")
            out.append((start, stop))
            cursor = stop
        return out
    finally:
        os.close(fd)


def _frame(payload: bytes) -> bytes:
    return BHDR.pack(
        BMAGIC, CODEC_RAW, 0, 0, len(payload), len(payload), 0,
        binascii.crc32(payload) & 0xFFFFFFFF, hashlib.sha256(payload).digest()
    ) + payload


def _run_variant(root: Path, a_suffix: bytes, b_prefix: bytes) -> dict:
    name = f"split-{len(a_suffix)}-{len(b_prefix)}"
    path = root / name
    control_pos = _C + 128
    expected_ghost = _B - len(a_suffix)
    with path.open("wb") as stream:
        stream.truncate(_SIZE)
        stream.seek(_A - len(a_suffix))
        stream.write(a_suffix)
        stream.seek(_B)
        stream.write(b_prefix + bytes(BHDR.size + 16))
        stream.seek(control_pos)
        stream.write(_frame(b"authentic-candidate-control"))
        stream.flush()
        os.fsync(stream.fileno())

    extents = _extents(path)
    # This is not a green test of the hypothesis if the filesystem maps the
    # source as a single continuous DATA region; require a real logical hole.
    first = next(((lo, hi) for lo, hi in extents if lo <= _A - len(a_suffix) < hi), None)
    second = next(((lo, hi) for lo, hi in extents if lo <= _B < hi), None)
    third = next(((lo, hi) for lo, hi in extents if lo <= control_pos < hi), None)
    if not (first and second and third and first[1] < second[0] and second[1] < third[0]):
        raise RuntimeError(f"UNSUPPORTED: no distinct nonadjacent extents: {extents}")

    baseline = recover_blob_records(path)
    alternate, direct_metrics = sparse_candidates(path, admit=False)
    admitted, admission_metrics = sparse_candidates(path)
    forced_fallback, fallback_metrics = sparse_candidates(path, force_unsupported=True)

    baseline_offsets = [r["offset"] for r in baseline]
    alternate_offsets = [r["offset"] for r in alternate]
    assert baseline_offsets == [control_pos], ("incumbent unexpected", baseline_offsets)
    assert forced_fallback == baseline and fallback_metrics["route"] == "bounded-fallback"
    assert direct_metrics["route"] == admission_metrics["route"] == "sparse-seeks", (
        direct_metrics, admission_metrics
    )
    assert admitted == alternate, ("admission changed scientific behavior", admission_metrics)
    # Retain the falsified O1 layout as a positive regression control.
    assert alternate_offsets == baseline_offsets, (
        "disjoint-extent parity regression", alternate_offsets, baseline_offsets
    )
    assert expected_ghost not in alternate_offsets, "phantom offset was admitted"

    with path.open("rb") as src:
        src.seek(expected_ghost)
        actual_magic = src.read(4)
    assert actual_magic != BMAGIC
    assert alternate[0]["verification"] == "unverified"
    assert alternate[0]["generation_membership"] == "unknown"
    return {
        "layout": name,
        "logical_bytes": _SIZE,
        "allocated_bytes": path.stat().st_blocks * 512,
        "reported_data_extents": extents,
        "baseline_offsets": baseline_offsets,
        "sparse_offsets": alternate_offsets,
        "hypothesized_phantom_offset": expected_ghost,
        "actual_ghost_magic_hex": actual_magic.hex(),
        "on_disk_magic_is_not_real_header": actual_magic != BMAGIC,
        "phantom_was_returned": expected_ghost in alternate_offsets,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "fallback_route": fallback_metrics["route"],
        "admission_route": admission_metrics["route"],
        "decision": "EXACT_PARITY_PRESERVED_OVER_DISJOINT_EXTENT_MAGIC_SPLIT",
    }


def main() -> None:
    report = {
        "question": "Does the authentic oracle already reject physical split-magic across sparse holes?",
        "original_hypothesis": "FALSIFIED_IN_EARLIER_EXACT_SOURCE_RUN_40040863477",
        "evidence_tier": "exact-source hosted scientific negative; not a product change",
        "source_oracle_git_blob": "94fc2234df0035938be3151dfaa5eef7bc317598",
        "source_scanner_git_blob": "94c25029fdd167c00871aabbe8fe90fbe7490026",
        "variants": [],
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-sparse-gap-court-") as d:
        root = Path(d)
        for a_suffix, b_prefix in ((b"CMA", b"4"), (b"CM", b"A4"), (b"C", b"MA4")):
            report["variants"].append(_run_variant(root, a_suffix, b_prefix))
    report["decision"] = "DISJOINT_EXTENT_SPLIT_MAGIC_REGRESSION_PARITY_PASS"
    report["limits"] = [
        "no product repair or migration",
        "source filesystem may not support coherent SEEK_DATA/SEEK_HOLE",
        "synthetic framing not authenticated recovery",
        "no concurrent mutation or cross-platform claim",
        "no timing, size, or compression product credit",
    ]
    print(json.dumps(report, sort_keys=True, indent=2))
    print("SCIENTIFIC_DISCONTIGUOUS_EXTENT_PARITY_CONFIRMED")


if __name__ == "__main__":
    main()
