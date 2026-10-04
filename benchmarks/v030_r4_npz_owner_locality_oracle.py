from __future__ import annotations

"""Hostile locality falsifier for the exact NPZ->external-NPY R4 owner.

The complementary Analytics dual-owner seed is a major density win, but its research wrapper stores
`features_compressed.npz` as one authenticated owner and reconstructs external `features.npy` from an
ordinary DEFLATE member. This oracle asks whether that representation can honestly satisfy the existing
<=8x cold stored-byte selective-read target *without* adding a new seek structure.

It intentionally gives the candidate two views:
  1. the current research-wrapper boundary, which authenticates the complete NPZ component; and
  2. an optimistic member-payload lower bound that ignores ZIP framing and hashes and charges only the
     member's compressed DEFLATE payload.

If even the optimistic end-range path is >8x for a 4 KiB read, naive promotion is falsified and the
proper response is rehabilitation (restart points/chunking/range proofs/other representation), not
weakening locality. No shipping format, selector or version changes are made here.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path
import time
import zipfile

from benchmarks import neutral_hostile_corpus_v1 as NEUTRAL
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL

SCHEMA = "cmpct-v030-r4-npz-owner-locality-v1"
REQUEST = 4096
MAX_COLD_STORED_AMP = 8.0


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    NEUTRAL.corpus_analytics(work)
    source = work / "04_analytics_and_database"
    relation = DUAL._npz_relation(source)["accepted"]
    npz = source / relation["npz_path"]
    npy = source / relation["npy_path"]
    raw = npy.read_bytes()

    with zipfile.ZipFile(npz, "r") as zf:
        info = zf.getinfo(relation["member"])
        if info.file_size != len(raw):
            raise RuntimeError("NPZ member length differs from external NPY")
        full = zf.read(info.filename)
        if full != raw:
            raise RuntimeError("NPZ member differs from external NPY")

    length = min(REQUEST, len(raw))
    starts = sorted({0, max(0, len(raw)//2 - length//2), max(0, len(raw)-length)})
    requests = []
    for start in starts:
        # Standard ZIP semantics have no DEFLATE restart index here. For a hostile product review we
        # execute the ordinary exact path and retain both the measured complete-member decoded work and
        # an optimistic physical bound that charges only compressed member payload bytes.
        c0 = time.process_time(); w0 = time.perf_counter()
        with zipfile.ZipFile(npz, "r") as zf:
            reconstructed = zf.read(info.filename)
        cpu = time.process_time() - c0; wall = time.perf_counter() - w0
        got = reconstructed[start:start+length]
        if got != raw[start:start+length]:
            raise RuntimeError("range reconstruction mismatch")
        requests.append({
            "start": start,
            "length": length,
            "sha256": _sha(got),
            "decoded_member_bytes": len(reconstructed),
            "decoded_logical_amplification": len(reconstructed) / max(1, length),
            "optimistic_member_payload_bytes": int(info.compress_size),
            "optimistic_member_payload_amplification": int(info.compress_size) / max(1, length),
            "current_wrapper_npz_bytes": npz.stat().st_size,
            "current_wrapper_cold_stored_amplification": npz.stat().st_size / max(1, length),
            "standard_reader_cpu_s": cpu,
            "standard_reader_wall_s": wall,
        })

    max_optimistic = max(r["optimistic_member_payload_amplification"] for r in requests)
    max_wrapper = max(r["current_wrapper_cold_stored_amplification"] for r in requests)
    supported = max_optimistic <= MAX_COLD_STORED_AMP
    return {
        "schema": SCHEMA,
        "relation": relation,
        "npz_bytes": npz.stat().st_size,
        "npy_bytes": npy.stat().st_size,
        "zip_member": {
            "filename": info.filename,
            "compression_method": int(info.compress_type),
            "compressed_bytes": int(info.compress_size),
            "uncompressed_bytes": int(info.file_size),
            "crc32": int(info.CRC),
        },
        "request_bytes": length,
        "requests": requests,
        "max_optimistic_member_payload_amplification": max_optimistic,
        "max_current_wrapper_cold_stored_amplification": max_wrapper,
        "locality_ceiling": MAX_COLD_STORED_AMP,
        "hypothesis": {
            "naive_owner_meets_8x_cold_stored_target": supported,
            "naive_owner_requires_rehabilitation": not supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "same_exact_npz_npy_relation": True,
            "optimistic_bound_ignores_zip_framing_and_authentication": True,
            "current_wrapper_authenticates_whole_npz_component": True,
            "no_physical_range_io_claim": True,
            "no_threshold_sweep": True,
        },
        "next_if_falsified": "preserve density seed; add bounded restart/chunk/range-proof design or change owner boundary, then remeasure physical selective I/O",
        "next_if_supported": "independently instrument physical reads before any product locality claim",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-npz-locality-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-npz-locality.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({
        "member": d["zip_member"],
        "max_optimistic_member_payload_amplification": d["max_optimistic_member_payload_amplification"],
        "max_current_wrapper_cold_stored_amplification": d["max_current_wrapper_cold_stored_amplification"],
        "hypothesis": d["hypothesis"],
    }, indent=2))


if __name__ == "__main__":
    main()
