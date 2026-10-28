from __future__ import annotations

"""Accounting-corrected dependency-cone falsifier for the Analytics Mode2 dual-view repair.

V1 intentionally exercised the first concrete dual-view bundle, but hostile review found an accounting
mismatch in its selective-read helper: it rehashed unrelated base/NPY/tabular components while only
charging the NPZ dependency-cone bytes. That makes V1 useful for storage economics but not authoritative
for cold selective I/O.

V2 changes no representation, thresholds, segment size, stored bytes, or preregistered decision law.
It only makes the cold-read integrity boundary explicit: `auth.bin` is the small archive-root/header
object for this research wrapper. A selective NPZ read consumes and charges that root, the manifest,
NPZ metadata, touched NPZ segments and Merkle sibling nodes. It verifies the manifest and NPZ-meta
digests anchored in the root, then verifies touched segments to the anchored NPZ Merkle root. It does
not read or rehash base.cmpct, npy.cmpct, or owner.tcol because they are outside the NPZ read dependency
cone. Full extraction still validates those components through V1's complete-bundle verification.

This remains diagnostic research packaging, not a claim that `auth.bin` is the final product's
cryptographic root layout. The product prototype must embed the same dependency-cone property in the
actual authenticated format before promotion.
"""

import argparse
import json
import os
from pathlib import Path

from benchmarks import v030_r4_mode2_dual_view_locality as V1

SCHEMA = "cmpct-v030-r4-mode2-dual-view-locality-v2"
AUTH_DIGESTS = 5


def _cold_authenticated_range(bundle: Path, start: int, length: int) -> tuple[bytes, dict]:
    raw_path = bundle / "owner.npz"
    meta = (bundle / "npz.meta").read_bytes()
    auth = (bundle / "auth.bin").read_bytes()
    manifest = (bundle / "manifest.json").read_bytes()

    magic, logical, seg_bytes, leaves, _root = V1.META.unpack(meta)
    if magic != V1.MAGIC or start < 0 or length < 0 or start + length > logical:
        raise ValueError("invalid NPZ range")

    expected_auth_bytes = len(V1.MAGIC) + AUTH_DIGESTS * 32
    if len(auth) != expected_auth_bytes or auth[: len(V1.MAGIC)] != V1.MAGIC:
        raise ValueError("invalid dual-view root/header")
    p = len(V1.MAGIC)
    digests = [auth[p + i * 32 : p + (i + 1) * 32] for i in range(AUTH_DIGESTS)]
    if digests[0] != V1._sha(manifest):
        raise ValueError("manifest root mismatch")
    if digests[4] != V1._sha(meta):
        raise ValueError("NPZ metadata root mismatch")

    first = start // seg_bytes
    last = (start + max(0, length - 1)) // seg_bytes if length else first
    out = bytearray()
    touched_data = 0
    proof_bytes = 0
    with open(raw_path, "rb", buffering=0) as rf, open(bundle / "npz.tree", "rb", buffering=0) as tf:
        for idx in range(first, last + 1):
            off = idx * seg_bytes
            seg = os.pread(rf.fileno(), min(seg_bytes, logical - off), off)
            ok, pb = V1._verify_segment_with_file(tf.fileno(), meta, idx, seg)
            if not ok:
                raise ValueError("NPZ segment authentication failed")
            touched_data += len(seg)
            proof_bytes += pb
            a = max(start, off) - off
            b = min(start + length, off + len(seg)) - off
            if b > a:
                out.extend(seg[a:b])

    root_header_bytes = len(auth)
    dependency_metadata_bytes = len(meta) + len(manifest)
    touched = touched_data + proof_bytes + root_header_bytes + dependency_metadata_bytes
    return bytes(out), {
        "requested_bytes": length,
        "data_segment_bytes": touched_data,
        "proof_bytes": proof_bytes,
        "root_header_bytes": root_header_bytes,
        "dependency_metadata_bytes": dependency_metadata_bytes,
        "physical_bytes_touched": touched,
        "amplification": touched / max(1, length),
        "segments_touched": last - first + 1,
        "unrelated_component_bytes_read": 0,
    }


def run(work: Path) -> dict:
    # Preserve the V1 representation/build/full-verification path exactly; replace only the selective
    # dependency-cone reader whose accounting was challenged by hostile review.
    original = V1._cold_authenticated_range
    V1._cold_authenticated_range = _cold_authenticated_range
    try:
        d = V1.run(work)
    finally:
        V1._cold_authenticated_range = original

    d["schema"] = SCHEMA
    d["contract"].update({
        "v1_storage_representation_unchanged": True,
        "cold_npz_dependency_cone_excludes_unrelated_component_rehash": True,
        "unrelated_component_bytes_read_per_npz_range": 0,
        "research_root_header_not_final_product_crypto_layout": True,
        "hostile_review_fix_only_no_threshold_or_representation_change": True,
    })
    d["hostile_review"] = {
        "v1_issue": "selective helper physically rehashed base.cmpct/npy.cmpct/owner.tcol but did not charge those unrelated reads",
        "v2_fix": "anchor NPZ dependency cone in charged small auth/header; verify manifest/meta roots plus touched Merkle path only",
        "scientific_effect": "storage economics unchanged; only V2 selective-I/O measurement may be used as locality evidence",
    }
    return d


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-mode2-dual-view-v2-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-mode2-dual-view-v2.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(json.dumps({
        "ordinary_v030_bytes": d["ordinary_v030_bytes"],
        "mode2_bytes": d["mode2_bytes"],
        "candidate_bytes": d["candidate_bytes"],
        "accepted_v029_bytes": d["accepted_v029_bytes"],
        "candidate_extra_vs_mode2_bytes": d["candidate_extra_vs_mode2_bytes"],
        "candidate_margin_vs_v029_bytes": d["candidate_margin_vs_v029_bytes"],
        "max_cold_authenticated_npz_amplification": d["max_cold_authenticated_npz_amplification"],
        "corruption_rejected": d["corruption_rejected"],
        "hypothesis": d["hypothesis"],
        "hostile_review": d["hostile_review"],
    }, indent=2))


if __name__ == "__main__":
    main()
