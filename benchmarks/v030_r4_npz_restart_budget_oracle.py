from __future__ import annotations

"""Budget falsifier for a straightforward zran-style rehabilitation of the NPZ owner.

The dual-owner seed has 1,681,985 bytes of Analytics density margin versus the accepted v0.29
artifact, but the exact NPZ owner has ~868x cold stored-byte amplification for a 4 KiB external-NPY
read. A conventional random-access DEFLATE index restores from periodic checkpoints carrying inflate
state and up to the 32 KiB history window. This diagnostic asks whether a straightforward full-window
checkpoint design can fit inside the *existing density margin* while forcing at most 8x compressed
traversal per 4 KiB request.

It is deliberately not an impossibility proof. A representation with smaller sufficient state,
shared/delta-coded checkpoints, different ownership, or a stronger range proof may beat this bound.
It only prevents us from pretending that a textbook full-window restart index is free.
"""

import argparse
import json
import math
from pathlib import Path
import shutil
import zlib
import zipfile

from benchmarks import neutral_hostile_corpus_v1 as NEUTRAL
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL

SCHEMA = "cmpct-v030-r4-npz-restart-budget-v1"
REQUEST_BYTES = 4096
MAX_STORED_AMP = 8.0
WINDOW_BYTES = 32768
MARGIN_VS_V029_BYTES = 1_681_985


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    NEUTRAL.corpus_analytics(work)
    source = work / "04_analytics_and_database"
    rel = DUAL._npz_relation(source)["accepted"]
    npz = source / rel["npz_path"]
    with zipfile.ZipFile(npz, "r") as zf:
        info = zf.getinfo(rel["member"])
        member = zf.read(info.filename)

    max_traverse = int(REQUEST_BYTES * MAX_STORED_AMP)
    checkpoints = max(0, math.ceil(info.compress_size / max_traverse) - 1)

    # Approximate the history material a full-window checkpoint family would carry. Compressed and
    # uncompressed stream positions are not linear in general; proportional placement is used only to
    # sample this concrete high-entropy member's dictionary compressibility, not as a seek algorithm.
    windows = []
    positions = []
    for i in range(1, checkpoints + 1):
        pos = min(len(member), max(WINDOW_BYTES, round(i * len(member) / (checkpoints + 1))))
        start = max(0, pos - WINDOW_BYTES)
        w = member[start:pos]
        if len(w) < WINDOW_BYTES:
            w = bytes(WINDOW_BYTES - len(w)) + w
        windows.append(w)
        positions.append(pos)
    raw_state = b"".join(windows)
    # Whole-family compression is intentionally favorable: it allows cross-checkpoint redundancy that
    # independent checkpoint records would not automatically get.
    compressed_family = zlib.compress(raw_state, 9) if raw_state else b""

    raw_over = len(raw_state) - MARGIN_VS_V029_BYTES
    compressed_over = len(compressed_family) - MARGIN_VS_V029_BYTES
    return {
        "schema": SCHEMA,
        "npz_bytes": npz.stat().st_size,
        "member_compressed_bytes": int(info.compress_size),
        "member_uncompressed_bytes": int(info.file_size),
        "request_bytes": REQUEST_BYTES,
        "locality_ceiling": MAX_STORED_AMP,
        "max_compressed_traversal_per_request_bytes": max_traverse,
        "checkpoint_count_required_by_spacing": checkpoints,
        "deflate_window_bytes_per_checkpoint": WINDOW_BYTES,
        "raw_full_window_state_bytes": len(raw_state),
        "whole_family_zlib9_bytes": len(compressed_family),
        "whole_family_zlib9_ratio": (len(compressed_family) / len(raw_state)) if raw_state else 0.0,
        "analytics_margin_vs_v029_bytes": MARGIN_VS_V029_BYTES,
        "raw_state_budget_overage_bytes": raw_over,
        "compressed_state_budget_overage_bytes": compressed_over,
        "hypothesis": {
            "straight_full_window_checkpoints_fit_raw_margin": raw_over <= 0,
            "straight_full_window_checkpoints_fit_even_after_favorable_global_zlib9": compressed_over <= 0,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "not_an_impossibility_proof": True,
            "proportional_windows_only_estimate_state_compressibility": True,
            "global_checkpoint_compression_is_favorable_to_candidate": True,
            "bit_alignment_and_other_inflate_state_not_charged": True,
            "no_threshold_sweep": True,
        },
        "next_if_falsified": "do not build textbook full-window checkpoints; investigate smaller sufficient state, checkpoint delta/reuse, changed owner boundary, or independent chunked view under the same density/locality budget",
        "next_if_supported": "build an exact restart prototype and measure physical reads, state bytes, CPU, recovery and portability",
        "sampled_uncompressed_positions": positions,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-npz-restart-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-npz-restart-budget.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({k:d[k] for k in (
        "checkpoint_count_required_by_spacing", "raw_full_window_state_bytes", "whole_family_zlib9_bytes",
        "analytics_margin_vs_v029_bytes", "raw_state_budget_overage_bytes", "compressed_state_budget_overage_bytes", "hypothesis")}, indent=2))


if __name__ == "__main__":
    main()
