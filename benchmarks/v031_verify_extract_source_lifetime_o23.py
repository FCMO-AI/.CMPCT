#!/usr/bin/env python3
"""O23: precise same-inode source-lifetime falsifier for verify(); extractall().

This experiment is deliberately not an implementation of a transactional or
SHA-authenticated extractor. See the separately committed O23 preregistration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

from cmpct.codec import BHDR, sha
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from v031_pack_physical_sha_court import archive_bytes


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def view(dest: Path, packed: bool) -> bytes:
    if packed:
        return (dest / "alpha.md").read_bytes() + (dest / "beta.md").read_bytes()
    return (dest / "direct.md").read_bytes()


def must_reject_sha(archive: Path, packed: bool) -> str:
    with CMPCT(archive) as fresh:
        # CRC-tier member decoding must remain viable; otherwise a rejection
        # is an uninformative fixture defect instead of a SHA-tier contrast.
        readback = (
            fresh.read("alpha.md") + fresh.read("beta.md")
            if packed else fresh.read("direct.md")
        )
        try:
            fresh.verify()
        except (OSError, IOError, ValueError) as exc:
            required = (
                "physical PACK SHA-256 verification failure"
                if packed else "SHA-256 verification failure"
            )
            assert required in str(exc), (
                f"wrong rejection cause: required={required!r}, got={exc!r}"
            )
            return digest(readback)
        raise AssertionError("fresh Reader incorrectly verified SHA-inconsistent source")


def in_place(fd: int, image: bytes) -> None:
    # No truncation or inode rebinding. A writer with permission to change the
    # original inode runs after verify and before extraction, deterministically.
    pos = 0
    while pos < len(image):
        sent = os.pwrite(fd, image[pos:pos + 1024 * 1024], pos)
        if sent <= 0:
            raise OSError("short or zero pwrite during controlled source mutation")
        pos += sent
    os.fsync(fd)


def one_case(root: Path, *, packed: bool, original: bytes, altered: bytes) -> dict:
    label = ("micro_pack_128" if len(original) == 128 else "pack_4mib") if packed else ("raw_128" if len(original) == 128 else "direct_raw_4mib")
    assert len(original) == len(altered)
    assert original != altered and len(original) % 2 == 0
    original_image = archive_bytes(original, original, packed=packed)
    mutated_image = archive_bytes(original, altered, packed=packed)
    assert len(original_image) == len(mutated_image)
    assert original_image != mutated_image

    baseline = root / (label + "-control.cmpct")
    baseline.write_bytes(original_image)
    control_destination = root / (label + "-control-out")
    with CMPCT(baseline) as control:
        assert control.verify() == (2 if packed else 1)
        control.extractall(control_destination, metadata=False)
    assert view(control_destination, packed) == original

    target = root / (label + "-mutable.cmpct")
    target.write_bytes(original_image)
    structural = preflight_archive(target)
    assert structural["blobs"] == 1, structural
    destination = root / (label + "-mutated-out")
    before_image_sha = digest(original_image)
    assert digest(target.read_bytes()) == before_image_sha
    expected_physical_sha = sha(original)

    with CMPCT(target) as reader:
        record_start = reader.record_base + int(reader.blobs[0][0])
        record_end = record_start + BHDR.size + len(original)
        first = BHDR.unpack_from(original_image, record_start)
        second = BHDR.unpack_from(mutated_image, record_start)
        assert bytes(first[-1]) == bytes(second[-1]) == expected_physical_sha
        assert int(first[-2]) != int(second[-2]), (
            "CRC field must be repaired for modified payload"
        )
        deltas = [i for i, (a, b) in enumerate(zip(original_image, mutated_image))
                  if a != b]
        assert deltas and min(deltas) >= record_start and max(deltas) < record_end
        assert original_image[:record_start] == mutated_image[:record_start]
        assert original_image[record_end:] == mutated_image[record_end:]
        assert reader.verify() == (2 if packed else 1)
        cached_before_mutation = sorted(reader.cache)
        fd = os.open(target, os.O_RDWR)
        try:
            before = os.fstat(fd)
            held = os.fstat(reader.f.fileno())
            assert (before.st_dev, before.st_ino) == (held.st_dev, held.st_ino)
            assert before.st_size == len(original_image)
            in_place(fd, mutated_image)
            after = os.fstat(fd)
            held_after = os.fstat(reader.f.fileno())
            assert ((before.st_dev, before.st_ino, before.st_size) ==
                    (after.st_dev, after.st_ino, after.st_size) ==
                    (held_after.st_dev, held_after.st_ino, held_after.st_size))
        finally:
            os.close(fd)

        # Confirm the mutated source and index remain structurally valid before
        # the same still-open Reader decides what to publish.
        assert digest(target.read_bytes()) == digest(mutated_image)
        assert preflight_archive(target)["blobs"] == 1
        extraction_error = None
        try:
            reader.extractall(destination, metadata=False)
        except (OSError, IOError, ValueError) as exc:
            extraction_error = f"{type(exc).__name__}: {exc}"

    physical_readback_sha = must_reject_sha(target, packed)
    assert physical_readback_sha == digest(altered), (
        "post-mutation ordinary read must see exactly CRC-repaired mutant"
    )
    if extraction_error is not None:
        published = "REJECTED"
        output_sha = None
    else:
        observed = view(destination, packed)
        output_sha = digest(observed)
        if observed == original:
            published = "ORIGINAL_VERIFIED"
        elif observed == altered:
            published = "MUTATED_UNVERIFIED"
        else:
            published = "OTHER_UNEXPECTED_BYTES"
    return {
        "case": label,
        "bytes_logical": len(original),
        "archive_bytes": len(original_image),
        "archive_original_sha256": before_image_sha,
        "archive_after_same_inode_mutation_sha256": digest(mutated_image),
        "source_inode_stable": True,
        "source_size_stable": True,
        "authenticated_index_and_physical_sha_unmodified": True,
        "crc_repaired_and_post_mutation_ordinary_read_exact": True,
        "physical_record_mutation_span": [min(deltas), max(deltas)],
        "first_strong_verify": "PASS",
        "fresh_mutant_strong_verify": "REJECT_EXACT_PHYSICAL_SHA",
        "same_handle_cache_indices_after_verify": cached_before_mutation,
        "unchanged_source_control": "PUBLISHED_EXACT",
        "same_handle_extraction": published,
        "same_handle_extraction_error": extraction_error,
        "same_handle_output_sha256": output_sha,
        "original_logical_sha256": digest(original),
        "mutant_logical_sha256": digest(altered),
    }


def court() -> dict:
    tiny = (b"source-lifetime-pack-A:" * 4)[:64] + (
        b"source-lifetime-pack-B:" * 4
    )[:64]
    assert len(tiny) == 128
    large = hashlib.shake_256(b"cmpct-O23-source-ownership-raw").digest(4 * 1024 * 1024)
    with tempfile.TemporaryDirectory(prefix="cmpct-o23-source-lifetime-") as directory:
        root = Path(directory)
        pack = one_case(
            root, packed=True, original=tiny,
            altered=tiny[:-1] + bytes([tiny[-1] ^ 1])
        )
        raw = one_case(
            root, packed=False, original=large,
            altered=large[:-1] + bytes([large[-1] ^ 1])
        )
        # O23b registered cross-factors BEFORE adding these two fixtures.
        small_raw = one_case(
            root, packed=False, original=tiny,
            altered=tiny[:-1] + bytes([tiny[-1] ^ 1])
        )
        large_pack = one_case(
            root, packed=True, original=large,
            altered=large[:-1] + bytes([large[-1] ^ 1])
        )
    predicted = (
        pack["same_handle_extraction"] == "ORIGINAL_VERIFIED"
        and raw["same_handle_extraction"] == "MUTATED_UNVERIFIED"
    )
    crossed = (
        small_raw["same_handle_extraction"] == "ORIGINAL_VERIFIED"
        and large_pack["same_handle_extraction"] == "MUTATED_UNVERIFIED"
    )
    # The harness must stay green for a genuine counterexample to the
    # prediction. "PASS" denotes valid controls, NOT a product promotion.
    return {
        "status": "PASS",
        "decision": (
            "VERIFY_THEN_EXTRACT_NOT_SOURCE_SNAPSHOT_FOR_LARGE_DIRECT_RAW"
            if predicted
            else "PREDICTION_FALSIFIED_OR_NARROWED_REVIEW_RAW_CASES"
        ),
        "predicted_specific_raw_publication": "MUTATED_UNVERIFIED",
        "predicted_specific_pack_publication": "ORIGINAL_VERIFIED",
        "all_fundamental_controls": "PASS",
        "o23b_decision": (
            "CACHE_SIZE_CROSSED_CAUSAL_PREDICTION_CONFIRMED"
            if crossed else "CACHE_SIZE_CROSS_PREDICTION_FALSIFIED_OR_NARROWED"
        ),
        "o23b_expected_small_direct_raw": "ORIGINAL_VERIFIED",
        "o23b_expected_large_pack": "MUTATED_UNVERIFIED",
        "classification": "RESEARCH_SOURCE_LIFETIME_ONLY",
        "source_pr": 258,
        "fixture_expected_git_blob": "2383bf9a8f7ce8a9a01028ccf1072169897df3f1",
        "cases": {
            "micro_pack": pack, "direct_raw": raw,
            "small_raw": small_raw, "large_pack": large_pack,
        },
        "limitations": [
            "Sequential authorized same-inode source rewrite, not concurrent malicious race proof",
            "Synthetic r24 direct RAW and PACK, one Linux host, no complete tree or portability proof",
            "Trust-model boundary, not a release/format or compression improvement",
            "No claim about source immutability when held by a distinct trusted process",
            "Index physical SHA is not third-party authentication",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    opts = parser.parse_args()
    result = court()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if opts.out:
        opts.out.parent.mkdir(parents=True, exist_ok=True)
        opts.out.write_text(encoded, encoding="utf-8")
    print(encoded)
