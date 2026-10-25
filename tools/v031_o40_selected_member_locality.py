#!/usr/bin/env python3
"""O40 read-only research: what does the shipping micro-PACK 8x proxy actually bound?

No Builder/Reader monkeypatch or changed parser is needed. Every observation uses
authentic revision-24 artifacts, a fresh Reader for the cold selected-member read,
and a separate Reader for strong whole-archive verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from cmpct.builder import Builder
from cmpct.codec import BHDR, CODEC_ZSTD, S_PACK
from cmpct.reader import CMPCT
from experiments.entropygraph_v030_release_product_base import (
    R24_RELEASE_DEFLATE_REUSE_MIN_BYTES,
    R24_RELEASE_MICRO_MAX_FILE_BYTES,
    _locality_bounded_r24_build,
)

SIZES = ((1, 753), (32, 768), (128, 512), (512, 512))
EPOCH_NS = 1_600_000_000_000_000_000


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for block in iter(lambda: inp.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def make_input(root: Path, small: int, large: int) -> dict:
    root.mkdir(parents=True)
    shared = b"sequential configurations, repeated stanza, value=alpha;\\n"
    payloads = {
        "small.txt": b"!" * small,
        "large.txt": (shared * ((large // len(shared)) + 1))[:large],
    }
    for name, raw in payloads.items():
        path = root / name
        path.write_bytes(raw)
        os.chmod(path, 0o644)
        os.utime(path, ns=(EPOCH_NS, EPOCH_NS))
    os.utime(root, ns=(EPOCH_NS, EPOCH_NS))
    return {name: {"bytes": len(raw), "sha256": digest(raw)} for name, raw in payloads.items()}


def observe(path: Path, expected: dict, require_shared: bool) -> dict:
    # Cold Reader: no verify(), no prefetch, no first read of large member.
    with CMPCT(path) as reader:
        small_row = reader.by["small.txt"]
        large_row = reader.by["large.txt"]
        small_storage, large_storage = small_row[6], large_row[6]
        both_pack = small_storage[0] == S_PACK and large_storage[0] == S_PACK
        same_owner = both_pack and small_storage[1] == large_storage[1]
        if require_shared and not same_owner:
            return {"admission": "NOT_SAME_S_PACK", "both_pack": both_pack,
                    "same_owner": same_owner, "archive_bytes": path.stat().st_size}
        if not both_pack:
            return {"admission": "NOT_S_PACK", "both_pack": False,
                    "same_owner": False, "archive_bytes": path.stat().st_size}
        owner_idx = int(small_storage[1])
        owner_usize = int(reader.blobs[owner_idx][1])
        owner_csize = int(reader.blobs[owner_idx][2])
        owner_codec = int(reader.blobs[owner_idx][3])
        calls = []
        original_blob = reader._blob

        def trace(idx: int) -> bytes:
            calls.append(idx)
            return original_blob(idx)

        reader._blob = trace
        if reader.cache:
            raise AssertionError("cold Reader cache is unexpectedly nonempty")
        actual = reader.read_range("small.txt", 0, expected["small.txt"]["bytes"])
        if digest(actual) != expected["small.txt"]["sha256"]:
            raise AssertionError("selected full-member bytes incorrect")
        if calls != [owner_idx]:
            raise AssertionError(f"unexpected blob decode closure: {calls}")
        cached = reader.cache.get(owner_idx)
        if cached is None or len(cached) != owner_usize:
            raise AssertionError("measured S_PACK physical owner was not fully materialized")
        # Independently reauthenticate the physical owner; current Reader.verify()
        # may not compare S_PACK physical SHA in this development lineage.
        header = BHDR.unpack_from(reader.mm, reader.record_base + reader.blobs[owner_idx][0])
        if digest(bytes(cached)) != bytes(header[-1]).hex():
            raise AssertionError("physical S_PACK SHA-256 mismatch")
        # Codec 1 is Zstd; for RAW the whole owner is materialized but not decompressed.
        small_bytes = int(expected["small.txt"]["bytes"])
        large_bytes = int(expected["large.txt"]["bytes"])
        row = {
            "admission": "SAME_PHYSICAL_OWNER" if same_owner else "DIFFERENT_S_PACK_OWNERS",
            "both_pack": both_pack,
            "same_owner": same_owner,
            "owner_blob_ordinal": owner_idx,
            "owner_uncompressed_bytes": owner_usize,
            "owner_compressed_bytes": owner_csize,
            "owner_codec": owner_codec,
            "owner_codec_is_zstd": owner_codec == CODEC_ZSTD,
            "physical_sha256_verified_independently": True,
            "small_full_member_bytes": small_bytes,
            "largest_member_bytes": large_bytes,
            "release_pack_target_bytes": min(2 * 1024 * 1024, 8 * large_bytes),
            "cold_owner_decoded_to_small_ratio": owner_usize / small_bytes,
            "cold_owner_physical_to_small_ratio": owner_csize / small_bytes,
            "cold_owner_decoded_to_largest_ratio": owner_usize / large_bytes,
            "over_eight_to_selected_small_member": owner_usize > 8 * small_bytes,
            "archive_bytes": path.stat().st_size,
            "archive_sha256": hash_file(path),
        }
    # Separate new instance verifies all physical SHA evidence (not a warm-up).
    with CMPCT(path) as verifier:
        if verifier.verify() != 2:
            raise AssertionError("strong verification did not cover exactly two regular members")
        for name, f in expected.items():
            if digest(verifier.read(name)) != f["sha256"]:
                raise AssertionError(f"wrong independent reconstruction: {name}")
    row["strong_verified"] = True
    return row


def run_case(work: Path, small: int, large: int) -> dict:
    case = work / f"s{small}-l{large}"
    expected = make_input(case / "source", small, large)
    source_hash_pre = digest(json.dumps(expected, sort_keys=True).encode())
    release = case / "release.cmpct"
    release_stats = dict(_locality_bounded_r24_build(case / "source", release))
    if int(release_stats["format_revision"]) != 24:
        raise AssertionError("not authentic r24 fallback")
    shipping = observe(release, expected, require_shared=True)
    # Stronger, simpler single-owner control. Two distinct files, same original
    # Builder + same source, one-field pack target change; research only.
    single = case / "single-owner.cmpct"
    builder = Builder(
        case / "source", deflate_reuse_min=R24_RELEASE_DEFLATE_REUSE_MIN_BYTES,
    )
    builder.micro_pack_max_file = R24_RELEASE_MICRO_MAX_FILE_BYTES
    builder.micro_pack_target = 1
    builder.build(single)
    control = observe(single, expected, require_shared=False)
    if control.get("admission") != "SAME_PHYSICAL_OWNER":
        # A singleton pack may have S_PACK storage but must be a different owner
        # for the second member. This is the intended causal control.
        pass
    else:
        raise AssertionError("singleton policy unexpectedly shared a physical owner")
    with CMPCT(single) as verifier:
        if verifier.verify() != 2:
            raise AssertionError("single-owner control failed whole-file SHA")
    source_hash_post = digest(json.dumps({
        name: {"bytes": (case / "source" / name).stat().st_size,
               "sha256": hash_file(case / "source" / name)}
        for name in expected
    }, sort_keys=True).encode())
    if source_hash_post != source_hash_pre:
        raise AssertionError("source tree changed during comparison")
    return {
        "case": f"{small}:{large}",
        "source_identity": source_hash_pre,
        "release": shipping,
        "singleton_control": control,
        "singleton_archive_bytes": single.stat().st_size,
        "singleton_minus_release_archive_bytes": single.stat().st_size - release.stat().st_size,
        "source_exact": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-head", type=str, default="")
    args = parser.parse_args()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if args.expected_head and head != args.expected_head:
        raise AssertionError(f"wrong source HEAD {head} != {args.expected_head}")
    with tempfile.TemporaryDirectory(prefix="cmpct-o40-") as d:
        rows = [run_case(Path(d), x, y) for x, y in SIZES]
    valid = all(row["release"].get("admission") == "SAME_PHYSICAL_OWNER"
                and row["release"]["strong_verified"]
                and row["release"]["owner_codec_is_zstd"]
                for row in rows)
    exposed = [row["case"] for row in rows
               if row["release"].get("over_eight_to_selected_small_member")]
    homogeneous = rows[-1]["release"]
    conclusion = (
        "SUPPORTED_SCOPE_SELECTED_MEMBER_GAP"
        if valid and len(exposed) >= 2
        and not homogeneous["over_eight_to_selected_small_member"]
        else "NOT_ESTABLISHED_OR_FALSIFIED"
    )
    output = {
        "schema": "cmpct-o40-cold-mixed-size-pack-locality-v1",
        "source_head": head,
        "product_blobs_expected": {
            "reader": "e716233403dabd0966863c45635e18fa5ac6afb8",
            "builder": "663ef0922992b1fbb8f19e6eea88d55c10a56044",
            "release_base": "b6b87b5c2b2f50fe53114ad3b5d228cd1e887367",
        },
        "hypothesis": "largest-member pack cap does not enforce <=8x per selected tiny member",
        "decision": conclusion,
        "cases_over_8": exposed,
        "cases": rows,
        "limitations": [
            "Deterministic decoded-owner work, not process RSS/wall/CPU.",
            "No broad native/Windows/macOS or 15x15 product comparator.",
            "Per-member amplification is separate from largest-member proxy.",
            "Source files are synthetic and not benchmark identity anchors.",
            "No product or release promotion credit; no encoder policy change.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True, indent=2) + chr(10))
    print(json.dumps(output, sort_keys=True))
    if not valid:
        raise SystemExit("INVALID SCIENTIFIC COURT: shipping output did not exercise expected shared Zstd owner")


if __name__ == "__main__":
    main()
